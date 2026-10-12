"""Groq Free integration. Account tier is attested locally, not inferred from a key."""
import os
import json
import time
from pathlib import Path

import requests

from .enrichment import PROMPT, SCHEMA, canonical, validate_catalogue

MODEL = "openai/gpt-oss-20b"


class ProviderFailure(RuntimeError):
    def __init__(self, reason, metadata):
        super().__init__(reason)
        self.safe_metadata = metadata


class GroqFreeProvider:
    name = "groq_free"

    def __init__(self, model=MODEL, max_output_tokens=800):
        if model != MODEL or not 1 <= max_output_tokens <= 2000:
            raise ValueError("Free research adapter requires the pinned model and 1-2000 output tokens")
        self.model, self.max_output_tokens = model, max_output_tokens

    def payload(self, record):
        validate_catalogue(record)
        return {"model": self.model, "temperature": 0,
                "max_completion_tokens": self.max_output_tokens,
                "messages": [{"role": "system", "content": PROMPT},
                             {"role": "user", "content": canonical({"properties": record["properties"]})}],
                "response_format": {"type": "json_schema", "json_schema": {
                    "name": "catalogue_enrichment", "strict": True, "schema": SCHEMA}}}

    def generate(self, record):
        if os.environ.get("GROQ_ACCOUNT_TIER") != "free":
            raise ValueError("Verify the organization is Free and set GROQ_ACCOUNT_TIER=free locally")
        key = os.environ.get("GROQ_API_KEY", "")
        if not key or key == "your_api_key_here":
            raise ValueError("Set GROQ_API_KEY locally")
        response = requests.post("https://api.groq.com/openai/v1/chat/completions",
                                 json=self.payload(record), timeout=(10, 45),
                                 headers={"Authorization": f"Bearer {key}"}, allow_redirects=False)
        if response.status_code != 200:
            try:
                error = response.json().get("error", {})
                code = error.get("code")
            except (ValueError, AttributeError):
                code = None
            # Never retain message/failed_generation: those can contain response text.
            safe_code = code if code in {"json_validate_failed", "rate_limit_exceeded",
                "invalid_api_key", "model_not_found", "context_length_exceeded"} else "unclassified"
            raise ProviderFailure(f"Groq HTTP {response.status_code}; no retry or paid fallback",
                                  {"http_status": response.status_code, "error_code": safe_code,
                                   "usage_unavailable": True})
        data = response.json()
        usage = data.get("usage", {})
        normalized = {k: usage[v] for k, v in [("input_tokens", "prompt_tokens"),
                                               ("output_tokens", "completion_tokens")] if v in usage}
        metadata = {"response_id": data.get("id"), "model_returned": data.get("model"),
                    "usage": normalized, "raw_usage": usage, "account_tier_attested": "free",
                    "billing_usd_assumed_free_tier": 0,
                    "rate_limits": {k: v for k, v in response.headers.items()
                                    if k.lower().startswith("x-ratelimit-")}}
        choices = data.get("choices", [])
        if len(choices) != 1 or choices[0].get("finish_reason") != "stop":
            raise ProviderFailure("Incomplete or ambiguous generation", {**metadata, "error_code": "incomplete_generation"})
        message = choices[0]["message"]
        if message.get("refusal") or message.get("tool_calls"):
            raise ProviderFailure("Refusal or unexpected tool request", {**metadata, "error_code": "refusal_or_tool_request"})
        try:
            output = json.loads(message["content"])
        except (ValueError, KeyError, TypeError):
            raise ProviderFailure("Invalid JSON response", {**metadata, "error_code": "json_validate_failed"}) from None
        return output, metadata


class QuotaPaused(RuntimeError):
    def __init__(self, reason, retry_after=None):
        super().__init__(reason)
        self.retry_after = retry_after


class FreeQuota:
    """Persistent conservative reservations; caller holds the shared cache lock.

    Rolling windows avoid timezone/reset guesses. Stop instead of sleeping or
    retrying; rerun later reuses successful caches. Other org clients can still
    consume quota, so provider 429 remains authoritative.
    """
    def __init__(self, path, provider, clock=time.time):
        self.path, self.provider, self.clock = Path(path), provider, clock

    def __call__(self, record, key):
        now = self.clock()
        rows = [json.loads(s) for s in self.path.read_text().splitlines()] if self.path.exists() else []
        recent = [r for r in rows if r["time"] > now - 86400]
        minute = [r for r in recent if r["time"] > now - 60]
        tokens = len(canonical(self.provider.payload(record)).encode()) + 1024 + self.provider.max_output_tokens
        # Reserve before sending. Daily exhaustion and oversized records never wait.
        if tokens > 7000:
            raise QuotaPaused("Record exceeds the conservative minute token allowance")
        if len(recent) >= 900 or sum(r["tokens"] for r in recent) + tokens > 180000:
            raise QuotaPaused("Local daily free quota exhausted; resume another day")
        if len(minute) >= 20 or sum(r["tokens"] for r in minute) + tokens > 7000:
            retry_after = max(0.1, min(r["time"] for r in minute) + 60 - now + 0.1)
            raise QuotaPaused("Local minute quota paused before any API call", retry_after)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(canonical({"time": now, "tokens": tokens, "cache_key": key}) + "\n")
