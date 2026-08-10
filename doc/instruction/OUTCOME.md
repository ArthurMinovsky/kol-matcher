# OUTCOME — Thai TikTok KOL Matcher (P0)

## Problem

Thai-market brands need a defensible way to shortlist TikTok KOLs. This project
demonstrates structured brand intelligence + deterministic four-factor creator
ranking with explicit evidence provenance, reproducible offline from committed
fixtures, and a polished evaluator-facing web UI.

This revision changes the demo input contract: the primary inputs are
**brand name + Facebook page URL** (website URL optional). Dr. Pong Clinic is
the committed test case; the demo generalizes to arbitrary brands. Because the
assessment is TikTok-focused, **Apify (TikTok scraper) is the priority live
provider for KOL data** when `APIFY_API_TOKEN` is configured.

## Expected Results

### O1 — Generalized input contract
- Input: brand name (required), Facebook page URL (required, validated as an
  http(s) facebook.com URL), campaign goal (required), website URL (optional).
- `POST /api/analyze` accepts `{brand_name, facebook_url, campaign_goal,
  website_url?}` and returns `AnalyzeResponse` (brand profile + Top-15
  recommendations + source status + limitations).

### O2 — Dr. Pong deterministic test case
- Typing the Dr. Pong brand name or its Facebook URL into the general form
  auto-routes to the committed fixture pipeline: zero network calls, zero API
  keys, identical output on every run.
- `GET /api/demo/drpong` continues to serve the same fixture pipeline.
- Default recommendation count is Top 15 (was Top 10).

### O3 — Offline general-brand path (no API keys)
- For arbitrary brands with no LLM keys, brand intelligence uses an
  industry-keyword dictionary (~8 industries: beauty, food, travel, fashion,
  fitness, tech, finance, gaming) over the brand name to produce a heuristic
  BrandProfile.
- Heuristic profiles are visibly labelled "low-confidence heuristic profile"
  in API (`limitations`) and UI (badge).
- Without `APIFY_API_TOKEN`, ranking runs against a committed mixed-industry
  synthetic demo pool (~20 creators spanning beauty/food/travel/fashion),
  clearly labelled synthetic in API and UI.

### O4 — LLM brand-extraction path (LLM keys present)
- Provider order: Typhoon (`TYPHOON_API_KEY`) first, Gemini
  (`GEMINI_API_KEY`) as fallback; both via OpenAI-compatible HTTP endpoints
  using httpx. Model names configurable via env vars.
- LLM output is schema-constrained, prompt-injection-guarded (user/scraped
  content delimited as untrusted), and Pydantic-validated into BrandProfile.
- LLM never determines ranking order; it only produces the brand profile.

### O5 — Apify TikTok creator provider (priority live KOL source)
- When `APIFY_API_TOKEN` is configured, the general analyze path discovers and
  enriches real TikTok creators via Apify as the **priority** KOL data source:
  keyword/hashtag search derived from the brand profile's Thai+English
  keywords, hard-capped result set (~30 candidates), strict timeout.
- The Apify actor id is configurable via env (`APIFY_TIKTOK_ACTOR`, sensible
  documented default); responses are normalized into `CreatorProfile` with
  missing metrics preserved as `None`.
- Scoring on the live path uses the documented keyword-overlap relevance
  fallback (no embeddings for live creators) — stated as a limitation.
- On Apify failure/timeout: `source_status.tiktok = "FAILED"` and the pipeline
  falls back to the labelled synthetic demo pool; fallback never masquerades
  as live data.
- No provider-specific assumptions leak into scoring code.

### O6 — Deterministic ranking quality
- Match Score = 0.45·relevance + 0.25·engagement + 0.15·thailand_relevance
  + 0.15·style_fit, all components 0..100, ranking on unrounded values.
- Tie-breaker: match DESC → relevance DESC → evidence coverage DESC →
  canonical username ASC.
- Dr. Pong fixture relevance uses committed embeddings (cosine).
- Canonical duplicate usernames are deduplicated; malformed creator records
  fail safe (skipped, surfaced in limitations, never crash the pipeline).

### O7 — Trust layer independence
- Evidence Coverage (0..100), Audience Verification (default "Unavailable"),
  and Recommendation Confidence (HIGH/MEDIUM/LOW) are computed and displayed
  independently; none of them modify Match Score or ordering.

### O8 — Evaluator frontend
- Single-page dashboard in the javstarfinder-derived dark theme: input card
  (brand name, Facebook URL, campaign goal, optional website) with prominent
  "Load Dr. Pong Demo" CTA; Brand Intelligence panel (observed vs inferred
  badges, provider provenance, heuristic-profile badge when applicable);
  Top-15 ranking with per-creator four-component scores, evidence coverage,
  confidence, and expandable explanation/limitations/scoring evidence.
- All API calls go through `apps/web/lib/api.ts` using
  `NEXT_PUBLIC_API_BASE_URL` (default http://localhost:8000); no hardcoded
  endpoint URLs in components.
- Loading, error, and partial-data states are handled visibly.

### O9 — Dockerized evaluator experience
- `docker compose up --build` from a fresh checkout starts the complete app:
  web on http://localhost:3000, API on http://localhost:8000, docs at /docs.
- Ports publish only on 127.0.0.1; web waits on the API healthcheck; the data
  volume mounts read-only; no Postgres/Redis/Qdrant/workers.
- Missing optional keys never prevent startup; `docker compose build
  --no-cache` succeeds clean.

### O10 — Dr. Pong evaluation
- `tests/evaluation/` runner computes pairwise relevant-vs-irrelevant ordering
  accuracy and Precision@5 on the Dr. Pong fixture labels (17 relevant / 8
  plausible / 15 irrelevant).
- Acceptance: pairwise accuracy ≥ 90%, P@5 ≥ 80%.

### O11 — Documentation
- README leads with Docker quick start; documents architecture, AI vs
  deterministic responsibilities, the 45/25/15/15 formula, trust-layer
  independence, Apify provider behavior and fallback, evaluation results,
  fixture provenance, limitations, and ethical constraints.

## Acceptance Criteria

- From a fresh checkout: `cp .env.example .env && docker compose up --build`;
  open http://localhost:3000; click "Load Dr. Pong Demo"; BrandProfile, Top
  15, four score components, evidence/confidence, and cached/synthetic
  provenance are all visible.
- From the same form, entering an arbitrary brand without keys returns a
  heuristic-labelled brand profile and a Top-15 ranking over the mixed demo
  pool; with `APIFY_API_TOKEN`, the same form ranks real TikTok creators
  sourced via Apify with `source_status.tiktok = "LIVE"`.
- `pytest` passes in `apps/api/tests/` and `tests/evaluation/`; the
  evaluation command prints the Dr. Pong metrics table meeting O10 thresholds.
- `curl http://localhost:8000/api/health` returns 200;
  `docker compose build --no-cache` succeeds.

## Constraints

- LLM providers: Typhoon then Gemini only (no OpenAI dependency).
- Creator data providers: Apify (TikTok) only; Firecrawl / SearXNG / live
  Facebook scraping remain P1 stubs.
- No authentication, database, queues, microservices, or vector DB.
- Synthetic/cached data is always labelled; missing metrics stay `None`,
  never fabricated zeros; Thailand relevance never described as audience
  geography; secrets never committed; Apify calls are budget-capped and
  time-boxed.

## Non-goals

- Live website/Facebook scraping, generalized crawling, agent frameworks.
- Food/travel evaluation fixtures (replaced by the single mixed demo pool,
  which is not label-evaluated).
- P2 extras (Lightpanda, CSV, multimodal).
- Live-path embeddings (keyword-overlap fallback is the documented behavior).

## Failure Behavior

- Missing LLM keys → heuristic brand path (O3) with visible provenance.
- Missing/failing Apify → `FAILED` source status + labelled synthetic demo
  pool fallback; the pipeline continues.
- Malformed fixture/provider records are skipped and surfaced in
  `limitations`.
- Invalid Facebook URL → 400 with a human-readable error.

## Compatibility

- Existing scaffold (docker-compose, Dockerfiles, models, scorer, fixtures,
  tests) is preserved and extended, not rewritten. Existing public behavior
  of `GET /api/health` and `GET /api/demo/drpong` remains intact apart from
  the Top-15 default.

## Approval Record

- Resolved via grilling: generalized FB+brand-name input; Dr. Pong
  auto-route; offline industry-dictionary heuristic with badge; Typhoon →
  Gemini LLM priority; Apify as priority live TikTok KOL provider with
  labelled synthetic fallback; new ~20-creator mixed synthetic demo pool;
  Top 15; Dr. Pong-only evaluation.
- Status: APPROVED by user.
