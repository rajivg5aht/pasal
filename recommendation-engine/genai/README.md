# Genuine GenAI integration

The active CLI uses **Groq Free / openai/gpt-oss-20b**. It requires `--live`,
local credentials and explicit Free-tier attestation. Paid CLI usage is disabled.
The historical OpenAI adapter remains for reproducible contract tests only.
One actual Groq Free pilot has completed (see `docs/genai-pilot-evidence.json`).
It has an assistant grounding review; it is not independent quality or ranking evidence.

Official documentation checked on 12 October 2026:
- [Free limits](https://console.groq.com/docs/rate-limits): 30 requests/minute,
  1,000/day, 8,000 tokens/minute and 200,000/day for this model. Organization
  settings may differ; inspect actual Console limits before running.
- [Structured outputs](https://console.groq.com/docs/structured-outputs): this
  model supports strict JSON schema. Semantic grounding still requires review.
- [Models](https://console.groq.com/docs/models): the chosen model is a production
  model, avoiding dependence on a preview model.
- [Billing](https://console.groq.com/docs/billing-faqs): upgrading requires a
  payment method. Keep a Free organization, without upgrading or adding payment.

The client cannot independently verify account billing tier from a key. The local
attestation is a guard, not a billing guarantee. No automatic paid fallback,
redirect following, upgrades or retries are implemented. Local rolling quota
reservations use conservative margins and stop before dispatch when exhausted.
Use the same cache/quota directory for every run; other organization clients can
consume quota too. Resume later with the same command to reuse cached responses.

## Data path

1. Build a timestamp-preserving snapshot with
   `preprocessing/build_metadata_snapshot.py`. Its cutoff must be approved for
   the experiment; the current legacy-cutoff sample is development-only.
2. Feed its `catalogue.jsonl` to the adapter. Only an allowlisted property map is
   sent externally. Item ID, cutoff, source hash and all user evidence stay local.
3. Cache immutable responses by provider/model, token limit, prompt/schema hash,
   input facts, cutoff and provenance. Real responses carry usage, latency and
   response/model IDs. Test fixtures never count as research outputs.
4. Reject unsupported citations/numbers and malformed responses. All other
   generated prose remains pending factual review, since automatic checks cannot
   detect every hallucination. Anonymous IDs must not become invented product
   types, brands, materials, benefits, prices or Kathmandu claims.
5. Record an explicit review keyed to the exact cache key and output hash.
6. `build_enriched_features.py` exports identical item populations and base
   property features with/without approved generated prose. Failures or missing
   reviews use unchanged base features. It reports counts and tokens, never an
   invented ranking improvement.
7. Fit the same TF-IDF method and compare the equivalent switching configurations
   using the common approved protocol. That final H2 experiment is not yet run.

## Commands from the project root

```powershell
# Input validation only; no API key, network or spend required.
.\.venv\Scripts\python.exe recommendation-engine/genai/enrichment.py --input data/processed/metadata-snapshot-development-2026-10-11/catalogue.jsonl --cache data/enriched/development-cache --model openai/gpt-oss-20b --max-requests 50
```

Configure `GROQ_API_KEY` in the local process environment and
`GROQ_ACCOUNT_TIER=free` only after checking the account. The CLI does not load
`.env` automatically. Never paste a key into chat or commit it. Use the pinned
`--model openai/gpt-oss-20b` and add `--live --budget-usd 0` for real requests.
The example's development snapshot is not the final research dataset.

`explanations.py` combines the actual local strategy reason with a reviewed
model-generated catalogue description. It labels the two separately, rejects
mismatched item provenance, and falls back honestly when generated prose is
missing. No user profile is sent to the provider. Website integration remains
outstanding.

A cache lock prevents simultaneous writers. If interrupted, verify the process
has exited before removing its `.writer.lock`. Quota reservations remain after
failures; cached failed calls are not automatically retried.

Review JSONL record format (actual keys/hashes must come from the cached output):

```json
{"cache_key":"<exact cache key>","output_sha256":"<sha(output)>","approved":true,"reviewer":"<reviewer identifier>","rationale":"<specific comparison against source facts>"}
```

This technical grounding review is not a substitute for Figure 11's ethically
approved human explanation-quality assessment. Report factual-claim support,
hallucination/alignment rates and relevance with a documented rubric; do not
treat an automated schema pass or an approval count as those metrics.

The existing property-enhanced CSV remains a **non-generative baseline**. The
final experiment must include actual provider output before it can be described
as GenAI-enhanced.
