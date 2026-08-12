# OUTCOME — Truthful Prototype-Ready KOL Matcher

## Problem

The Thai TikTok KOL Matcher currently allows live analysis to fall back to synthetic creator data, conflates fixture data with cached/live data, renormalizes unavailable LLM evidence, and lacks sufficient provenance, evidence gates, runtime bounds, and responsive availability states.

The desired result is a truthful prototype: live analysis returns only evidence-qualified live recommendations or a sanitized failure; explicit offline fixtures remain reproducible and clearly labelled.

## Expected Results

### O1 — Truthful live/offline boundary

- `POST /api/analyze` returns recommendations only from accepted live provider records.
- If live TikTok discovery fails or no creator passes the evidence gate, the request fails closed with zero recommendations.
- The live path never loads or labels demo-pool creators.
- `GET /api/demo/drpong` and `POST /api/matching/score` remain explicit offline/lab paths.
- Offline responses use `result_origin = PROTOTYPE_FIXTURE`.
- Live responses use `result_origin = LIVE`.
- Static fixtures are never labelled `CACHED`.

### O2 — Minimum live evidence

Every accepted live creator has:

- a validated canonical username;
- a constructed TikTok profile URL;
- at least three distinct recent posts;
- a usable non-empty caption for each accepted post.

Malformed, duplicate, hashtag-only, profile-only, or insufficient records are rejected. One accepted creator is sufficient for a successful live response; zero accepted creators is a failure.

### O3 — Complete provenance

Every live analysis exposes sanitized provenance sufficient to explain what happened:

- provider attempts and order;
- selected provider;
- provider outcome/error code;
- records observed;
- creators accepted/rejected;
- capture time;
- request identifier;
- model availability and scoring mode.

Provenance never exposes credentials, cookies, authorization headers, raw upstream responses, filesystem paths, prompts, or raw exception text.

### O4 — Correct scoring semantics

When LLM judging is available:

```text
0.20 × BM25
+ 0.25 × LLM relevance
+ 0.25 × Engagement
+ 0.15 × Thailand signals
+ 0.15 × Style fit
```

When LLM judging is unavailable:

```text
0.20 × BM25
+ 0.00 × LLM relevance
+ 0.25 × Engagement
+ 0.15 × Thailand signals
+ 0.15 × Style fit
```

The incomplete result is not renormalized. Unavailable LLM evidence is numeric `0`, `available=false`, and displayed as `Unavailable`/`Not observed`; it must not render as a filled neutral bar.

BM25 remains LEKCut 1.0.0/DeepCut based and keeps algorithm key `bm25_v2_lekcut`.

### O5 — Evidence-aware factor behavior

- Engagement uses only valid recent post metrics, fixed calibration, and weighted median.
- Follower count is never used as an engagement substitute.
- Missing Engagement evidence scores `0` and displays `Not observed`.
- Thailand scoring uses observable content/location signals, including `has_thailand_location`.
- Thailand signals never claim audience geography.
- Missing Thailand evidence scores `0` and displays `Not observed`.
- Style Fit uses a controlled taxonomy and observable evidence.
- Missing Style evidence scores `0` and displays `Not observed`.
- A neutral style value is permitted only when the brand explicitly has no style preference.
- Thai low-signal variants such as `ง่าย`, `ง่ายๆ`, `ทำง่าย`, and `easy` are treated consistently by the versioned matcher.

### O6 — Reliable model and provider behavior

- Typhoon is attempted before Gemini when both are configured.
- Failover is bounded to one attempt per configured provider.
- Timeout, rate-limit, upstream, malformed-JSON, and schema-invalid responses are handled explicitly.
- Every provider response is schema-validated before use.
- Brand extraction may use a clearly marked partial heuristic result when model extraction is unavailable.
- LLM judge unavailability never fabricates a relevance contribution or contaminates later requests.
- Correctness-path process-global caches, including fixture-loader and judge caches, are absent.

### O7 — Safe and bounded request execution

- Required input fields remain `brand_name`, `facebook_url`, and `campaign_goal`; `website_url` remains optional.
- Invalid, credential-bearing, non-public, private-IP, reserved-host, or unsafe redirect URLs are rejected before crawling.
- DNS resolution and every redirect destination are validated.
- Requests, fetched bodies, provider results, prompt text, creator counts, post counts, and concurrent work are bounded.
- Every live analysis has a 60-second overall deadline and cancels unfinished child work.
- CORS uses explicit normalized origins, methods, and headers; wildcard origins are rejected.
- Rate/concurrency protection returns a sanitized `429` when limits are exceeded.
- Client errors do not expose stack traces, paths, secrets, raw provider errors, or internal topology.

### O8 — Honest accessible frontend

- The UI displays global `LIVE` or `PROTOTYPE FIXTURE` provenance.
- Failed live analysis clears stale recommendations and shows an actionable sanitized error.
- Per-card synthetic/demo source copy is removed.
- Missing Engagement, Thailand, and Style evidence shows `Not observed` with an empty bar.
- Unavailable LLM evidence shows `Unavailable` with an empty bar.
- Rationales remain immediately before their relevant score details.
- TikTok links are constructed from validated creator identities.
- The Beta pill, creator rows, score rows, and provenance remain usable at 320px, 768px, 1024px, and 1440px.
- Keyboard focus, semantic labels, expanded state, controlled regions, loading state, and error state are observable to assistive technologies.
- The Dr. Pong control remains autofill-only and does not submit or change the campaign goal.

### O9 — Preserved deterministic prototype paths

- `/api/demo/drpong` remains credential-free and deterministic.
- `/api/matching/score` remains deterministic and BM25-only.
- Existing benchmark thresholds remain pairwise accuracy ≥90% and Precision@5 ≥80%.
- Docker Compose remains loopback-bound and starts without optional credentials.
- Langflow remains outside the `/api/analyze` runtime dependency path.

## Machine-Visible Outputs

- `result_origin`: `LIVE` or `PROTOTYPE_FIXTURE`.
- Evidence records expose `score`, `available`, and human-readable display state.
- Stable sanitized error codes include:
  - `VALIDATION_ERROR`
  - `URL_NOT_ALLOWED`
  - `LIVE_PROVIDER_UNAVAILABLE`
  - `MINIMUM_EVIDENCE_UNAVAILABLE`
  - `REQUEST_DEADLINE_EXCEEDED`
  - `RATE_LIMITED`
  - `MODEL_UNAVAILABLE`
  - `FIXTURE_UNAVAILABLE`
- Live success responses contain no synthetic creators.
- Live failure responses contain zero recommendations.
- Fixture failure responses do not expose filesystem paths.

## Acceptance Criteria

- Focused backend tests cover validation, URL safety, provider ordering, minimum evidence, provenance, fail-closed behavior, scoring availability, cache isolation, and model failover.
- Full backend and evaluation suites pass without weakening benchmark thresholds.
- Frontend type-check and production build pass.
- Browser verification confirms live failure, explicit fixture provenance, no stale results, score availability states, responsive layouts, keyboard operation, and clean console output.
- Docker configuration, API health, deterministic endpoints, request deadlines, cleanup, and resource limits are verified.
- Security checks confirm SSRF/redirect rejection, strict CORS, bounded inputs/outputs, rate protection, sanitized errors, and absence of secret leakage.
- Existing npm audit and Langflow limitations are reported as separate residual risks if they remain unresolved; they are not silently waived.

## Constraints and Non-goals

- No KeyBERT, sentence-transformers, embeddings, transformer downloads, database, authentication, queues, or vector database.
- Browser collection remains opt-in and public-only.
- No stealth patches, CAPTCHA solving, proxy rotation, or access-control bypass.
- No production deployment or internet-facing exposure is implied by prototype readiness.
- No database migration is required.
- The current dirty worktree is preserved; no reset or unrelated cleanup is allowed.
- Existing required backend `campaign_goal` behavior and public health/demo endpoints remain compatible.

## Failure Behavior

- Invalid requests fail before downstream calls.
- Unsafe URLs fail before crawling.
- Brand-source or model extraction degradation is surfaced as partial provenance where permitted.
- TikTok provider failure or zero accepted creators returns a sanitized `503`/`504` and no recommendations.
- LLM judge failure leaves only BM25’s declared contribution and marks LLM evidence unavailable.
- Deadline expiry cancels pending work and returns a sanitized timeout response.
- Rate-limit rejection returns `429` without invoking providers.
- Fixture loading failure returns a sanitized fixture error and never falls back to live or synthetic data.

## Explicit Exclusions

- Do not force unrelated dependency upgrades.
- Do not fix the Langflow Chat Output limitation unless separately approved.
- Do not add authentication, persistence, or external deployment.
- Do not claim live-provider verification without live credentials.

## Approval Record

- Status: APPROVED by user.
- Supersedes the previous outcome that approved synthetic live fallback and neutral LLM renormalization.
- Execution basis: `/Users/aminovsky/Desktop/kol-matcher-prototype-readiness_decree.md`.
