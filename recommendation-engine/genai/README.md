# Genuine GenAI integration

`enrichment.py` contains a real OpenAI Responses API adapter. It makes no calls
unless invoked with `--live`, an explicit model, local credentials, request/token
limits, current prices and an authorized budget. Dry runs only validate inputs;
they do not produce pretend model outputs. The user currently has no API access.

The adapter follows the official [structured-output API guide](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=responses).
Requests use strict JSON schema; refusals/incomplete responses are rejected.
Schema conformance does not establish factual accuracy. `store: false` is set;
this does not claim that all provider retention is disabled.

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
.\.venv\Scripts\python.exe recommendation-engine/genai/enrichment.py --input data/processed/metadata-snapshot-development-2026-10-11/catalogue.jsonl --cache data/enriched/development-cache --model pending-provider-selection --max-requests 50
```

When access is available, configure `GENAI_API_KEY` in the local process
environment and choose a model supporting the contract. The script does not
automatically load `.env`. Never paste a key into chat or commit it. A live run
also needs `--live --budget-usd ... --input-usd-per-million ...
--output-usd-per-million ...`, using current provider prices and the authorized
budget. No paid run has been performed by this project pass.

Budget reservations are written before dispatch, remain charged against the
local allowance even on failure, and prevent automatic retries. This conservative
guard is not a provider-enforced billing cap; reconcile real usage/billing before
reporting monetary cost. Separate account/project limits should enforce the
actual provider budget. A cache lock prevents simultaneous writers. After an
interrupted process, verify it has exited before removing its `.writer.lock`.

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
