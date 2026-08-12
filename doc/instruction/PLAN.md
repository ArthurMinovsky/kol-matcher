# Truthful Prototype-Ready KOL Matcher Implementation Plan

> **For agentic workers:** Execute this plan task-by-task with test-first changes, review checkpoints, and fresh verification before completion.

**Goal:** Make live KOL analysis fail closed and evidence-truthful while preserving explicit deterministic fixture/lab paths and the existing BM25 benchmark contract.

**Architecture:** Keep the current FastAPI + Next.js + Docker Compose architecture. Add typed provenance/error/evidence contracts at the API boundary, enforce bounded provider orchestration and live evidence gates in the backend, keep fixture loading isolated from live requests, and make the frontend render availability/provenance from API state rather than inferred labels.

**Tech Stack:** Python 3.12 Docker runtime, FastAPI/Pydantic, httpx, existing TikTok Research/browser providers, Typhoon/Gemini OpenAI-compatible clients, LEKCut 1.0.0/DeepCut, Next.js/React/TypeScript, Docker Compose, pytest, BrowserOS.

---

## Authoritative Requirements

- Implement approved OUTCOME IDs `O1`–`O9`.
- Follow `/Users/aminovsky/Desktop/kol-matcher-prototype-readiness_decree.md`.
- Preserve `GET /api/demo/drpong`, `POST /api/matching/score`, `bm25_v2_lekcut`, benchmark thresholds, Dr. Pong autofill-only behavior, Docker loopback binding, and the dirty worktree.
- Do not add authentication, persistence, embeddings, queues, vector databases, stealth browsing, CAPTCHA solving, proxy rotation, or unrelated dependency upgrades.
- Do not claim live-provider verification without live credentials.

## Dependency Order

1. Define API, evidence, provenance, error, and bounded-input contracts.
2. Harden URL, redirect, CORS, deadline, rate, and resource boundaries.
3. Implement strict LLM failover and remove correctness caches.
4. Correct scoring and missing-evidence semantics.
5. Enforce TikTok normalization and the three-caption live evidence gate.
6. Remove live synthetic fallback and isolate fixture workflows.
7. Update frontend rendering, responsive layout, and accessibility states.
8. Update documentation, ADR, verification ledger, Docker checks, and final review.

## Task 1: Freeze API and evidence contracts

**Outcome IDs:** O1, O3, O4, O5, O7  
**Dependencies:** None

**Files:**
- Modify: `apps/api/app/models/api.py`
- Modify: `apps/api/app/models/brand.py`
- Modify: `apps/api/app/models/evidence.py`
- Modify: `apps/api/app/models/creator.py`
- Test: `apps/api/tests/test_response_contract.py`
- Test: `apps/api/tests/test_input_contract.py`

- [ ] Add typed `result_origin` values `LIVE` and `PROTOTYPE_FIXTURE`.
- [ ] Add typed provider-attempt/provenance fields for provider name, order, status, sanitized error code, records seen, accepted/rejected counts, and `captured_at`.
- [ ] Add explicit evidence availability fields: numeric `score`, `available`, and display state/value.
- [ ] Add stable error codes for validation, unsafe URLs, unavailable live evidence, minimum evidence failure, deadline expiry, rate limiting, model unavailability, and fixture failure.
- [ ] Bound request strings, URLs, creator lists, post lists, tag lists, and metric values with Pydantic validation; reject unexpected fields where existing clients permit it.
- [ ] Preserve existing required `campaign_goal` behavior and public response fields wherever compatibility is safe.
- [ ] Write failing contract tests for live/fixture origin, unavailable evidence, bounded inputs, and sanitized error shape.
- [ ] Run: `docker compose run --rm api sh -lc 'PYTHONPATH=/workspace/apps/api pytest apps/api/tests/test_response_contract.py apps/api/tests/test_input_contract.py -q'` and confirm the new tests fail before implementation.
- [ ] Implement the minimal models and validators.
- [ ] Re-run the same command and require all new tests to pass.

**Acceptance:** API models express live/fixture provenance, unavailable evidence, bounded input, and stable sanitized errors without breaking existing deterministic endpoints.

## Task 2: Harden URL, redirect, CORS, deadline, and abuse boundaries

**Outcome IDs:** O3, O7  
**Dependencies:** Task 1

**Files:**
- Modify: `apps/api/app/main.py`
- Modify: `apps/api/app/config.py`
- Modify: `apps/api/app/safety/url_safety.py`
- Modify: `apps/api/app/crawlers/facebook_crawler.py`
- Modify: `apps/api/app/crawlers/website_crawler.py`
- Test: `apps/api/tests/test_url_safety.py`
- Test: `apps/api/tests/test_crawlers.py`
- Test: `apps/api/tests/test_request_limits.py`

- [ ] Add a 60-second request-wide analysis deadline and cancellation path for child provider/model/browser work.
- [ ] Normalize, trim, deduplicate, and explicitly validate CORS origins; reject wildcard origins and use explicit methods/headers.
- [ ] Resolve hostname addresses and reject private, loopback, link-local, reserved, multicast, credential-bearing, non-HTTPS, and unsafe targets before fetching.
- [ ] Disable unrestricted redirect following; validate each redirect destination against the same SSRF and host policy.
- [ ] Enforce bounded request bodies, fetched response bytes, provider result counts, prompt text, creator/post counts, and concurrent work without adding a dependency.
- [ ] Add prototype-scoped rate/concurrency protection with deterministic `429` behavior and `Retry-After`.
- [ ] Add a request ID and generic error mapping so client responses contain no stack traces, paths, secrets, raw upstream errors, or cookies.
- [ ] Write failing tests for private-IP DNS resolution, redirect-to-private targets, credential URLs, oversized inputs/responses, denied CORS origins, deadline cancellation, and rate-limit rejection.
- [ ] Run: `docker compose run --rm api sh -lc 'PYTHONPATH=/workspace/apps/api pytest apps/api/tests/test_url_safety.py apps/api/tests/test_crawlers.py apps/api/tests/test_request_limits.py -q'` and confirm the new protections fail before implementation.
- [ ] Implement the controls while preserving the existing public URL acceptance behavior for valid configured sources.
- [ ] Re-run the focused command and require all safety tests to pass.

**Acceptance:** Unsafe requests fail before downstream calls; all live work is bounded, cancellable, rate-protected, and sanitized.

## Checkpoint A: Contract and boundary review

- [ ] Tasks 1–2 focused tests pass in the Python 3.12 Docker image.
- [ ] No source provider is called for invalid or unsafe inputs.
- [ ] The API contract does not expose raw exceptions or paths.
- [ ] Review the diff before starting model/scoring work.

## Task 3: Implement strict LLM failover and remove correctness caches

**Outcome IDs:** O4, O6  
**Dependencies:** Task 1 and Task 2

**Files:**
- Modify: `apps/api/app/services/llm_client.py`
- Modify: `apps/api/app/services/llm_judge.py`
- Modify: `apps/api/app/services/brand_extractor.py`
- Modify: `apps/api/app/providers/fixture_loader.py`
- Test: `apps/api/tests/test_llm_client.py`
- Test: `apps/api/tests/test_relevance_contract.py`
- Test: `apps/api/tests/test_fixture_loader.py`

- [ ] Remove `_judge_cache`, `_cache_key`, and any process-global judge-result reuse.
- [ ] Remove fixture-loader `lru_cache` usage from correctness paths and return fresh request-local model data.
- [ ] Represent configured Typhoon and Gemini providers as a fixed ordered list with validated HTTPS origins.
- [ ] Attempt each configured provider at most once per request; fail over on timeout, rate limit, upstream error, malformed JSON, or schema-invalid output.
- [ ] Validate provider response schemas before accepting extraction or judge results.
- [ ] Preserve heuristic brand extraction only as explicitly partial provenance when extraction models are unavailable.
- [ ] Return unavailable judge evidence with score `0`, `available=false`, and truthful rationale/status.
- [ ] Write failing tests proving Typhoon→Gemini ordering, malformed/schema-invalid failover, both-provider failure, no token leakage, failed-request non-poisoning, and fresh fixture objects.
- [ ] Run: `docker compose run --rm api sh -lc 'PYTHONPATH=/workspace/apps/api pytest apps/api/tests/test_llm_client.py apps/api/tests/test_relevance_contract.py apps/api/tests/test_fixture_loader.py -q'` and confirm the new tests fail before implementation.
- [ ] Implement the ordered failover and request-local behavior.
- [ ] Re-run the focused command and require all tests to pass.

**Acceptance:** Model/provider failure is bounded and observable; no correctness result or outage is reused across requests.

## Task 4: Correct scoring and evidence semantics

**Outcome IDs:** O4, O5  
**Dependencies:** Task 3

**Files:**
- Modify: `apps/api/app/services/scorer.py`
- Modify: `apps/api/app/services/ranker.py`
- Modify: `apps/api/app/services/text_processing.py`
- Modify: `apps/api/app/services/bm25_matcher.py`
- Test: `apps/api/tests/test_scorer.py`
- Test: `apps/api/tests/test_ranking.py`
- Test: `apps/api/tests/test_relevance_contract.py`
- Test: `apps/api/tests/test_thai_processing.py`

- [ ] Make available-LLM scoring use the exact declared weights: BM25 20%, LLM 25%, Engagement 25%, Thailand 15%, Style 15%.
- [ ] Make unavailable-LLM scoring use only the declared BM25 20% contribution without renormalizing the missing LLM 25%.
- [ ] Remove follower-count engagement fallback and fabricated metric defaults.
- [ ] Use only valid recent post metrics, fixed calibration, and weighted median.
- [ ] Make missing Engagement, Thailand, and Style evidence score `0` with `available=false` and `Not observed`.
- [ ] Include `has_thailand_location` in Thailand evidence and never interpret observable Thailand signals as audience geography.
- [ ] Apply controlled style taxonomy; allow neutral style only for an explicit no-preference brand state.
- [ ] Expand/version Thai low-signal variants and retain stable `bm25_v2_lekcut` behavior.
- [ ] Write failing tests for exact available/unavailable weights, missing factors, follower-only creators, invalid metrics, Thailand false/missing states, style no-preference, Thai variants, and deterministic ties.
- [ ] Run: `docker compose run --rm api sh -lc 'PYTHONPATH=/workspace/apps/api pytest apps/api/tests/test_scorer.py apps/api/tests/test_ranking.py apps/api/tests/test_relevance_contract.py apps/api/tests/test_thai_processing.py -q'` and confirm new assertions fail before implementation.
- [ ] Implement the smallest scoring changes that satisfy the tests.
- [ ] Re-run the focused command and require all tests to pass.

**Acceptance:** Scores are mathematically honest, missing evidence is visible, and ranking remains deterministic.

## Task 5: Enforce TikTok normalization and minimum live evidence

**Outcome IDs:** O1, O2, O3  
**Dependencies:** Task 1, Task 2, and Task 3

**Files:**
- Modify: `apps/api/app/providers/base.py`
- Modify: `apps/api/app/providers/tiktok.py`
- Modify: `apps/api/app/providers/official_tiktok.py`
- Modify: `apps/api/app/providers/browser_tiktok.py`
- Modify: `apps/api/app/providers/tiktok_normalizer.py`
- Test: `apps/api/tests/test_tiktok_providers.py`
- Test: `apps/api/tests/test_provider_provenance.py`

- [ ] Keep official TikTok Research API first and browser/CDP second.
- [ ] Validate external provider payloads, skip malformed records, enforce creator/post/result caps, and deduplicate creator/post identities.
- [ ] Construct TikTok profile URLs from validated usernames instead of trusting arbitrary external `href` values.
- [ ] Extend browser collection from profile links to profile evidence plus at least three recent captioned posts.
- [ ] Require one accepted creator with three distinct usable captions for success; return zero accepted creators when the gate fails.
- [ ] Record provider attempt order, status, selected provider, records seen, accepted/rejected counts, and capture time.
- [ ] Write failing tests for official-first ordering, browser fallback, missing/invalid credentials, malformed payloads, duplicate records, hashtag-only captions, profile-only records, two-post rejection, exactly-three-post acceptance, caps, and malicious links.
- [ ] Run: `docker compose run --rm api sh -lc 'PYTHONPATH=/workspace/apps/api pytest apps/api/tests/test_tiktok_providers.py apps/api/tests/test_provider_provenance.py -q'` and confirm the new evidence tests fail before implementation.
- [ ] Implement provider normalization and the evidence gate without stealth, CAPTCHA, proxy, or access-control bypass behavior.
- [ ] Re-run the focused command and require all tests to pass.

**Acceptance:** Live provider output cannot satisfy the pipeline without a canonical profile and three usable captions.

## Task 6: Remove live synthetic fallback and isolate fixture workflows

**Outcome IDs:** O1, O3, O9  
**Dependencies:** Task 4 and Task 5

**Files:**
- Modify: `apps/api/app/services/pipeline.py`
- Modify: `apps/api/app/main.py`
- Modify: `apps/api/app/services/ranker.py`
- Modify: `apps/api/app/providers/fixture_loader.py`
- Test: `apps/api/tests/test_source_status.py`
- Test: `apps/api/tests/test_live_fail_closed.py`
- Test: `apps/api/tests/test_matching_api.py`
- Test: `tests/evaluation/test_benchmark_brands.py`

- [ ] Remove `load_demo_pool_creators` from the live `/api/analyze` recovery path.
- [ ] Return sanitized `503`/`504` with zero recommendations when provider discovery or the evidence gate produces no accepted live creators.
- [ ] Preserve heuristic brand profile extraction as partial where permitted, but never substitute creator fixtures.
- [ ] Set `result_origin=LIVE` only for live creator results and `result_origin=PROTOTYPE_FIXTURE` for explicit fixture/lab endpoints.
- [ ] Ensure fixture failures return sanitized errors without filesystem paths and never fall back to live or synthetic data.
- [ ] Keep `/api/demo/drpong` deterministic and keep `/api/matching/score` BM25-only.
- [ ] Write failing tests proving live failure is fail-closed, fixture origin is explicit, fixture data is not `CACHED`, stale demo-pool behavior is gone, and matching-lab behavior is unchanged.
- [ ] Run: `docker compose run --rm api sh -lc 'PYTHONPATH=/workspace/apps/api pytest apps/api/tests/test_source_status.py apps/api/tests/test_live_fail_closed.py apps/api/tests/test_matching_api.py tests/evaluation/test_benchmark_brands.py -q'` and confirm old fallback assertions fail before replacement.
- [ ] Implement the pipeline separation and update tests to the approved behavior.
- [ ] Re-run the focused command and require all tests to pass.

**Acceptance:** `/api/analyze` can return live recommendations or a truthful failure, never a synthetic recovery response.

## Checkpoint B: Backend behavior review

- [ ] Tasks 3–6 focused tests pass.
- [ ] No process-global correctness cache remains.
- [ ] Live failure has zero recommendations and no fixture provenance.
- [ ] Explicit fixture/lab endpoints remain deterministic.
- [ ] Run the full backend/evaluation suite: `docker compose run --rm api sh -lc 'PYTHONPATH=/workspace/apps/api pytest apps/api/tests tests/evaluation -q'`.
- [ ] Run the evaluator and require pairwise accuracy ≥90% and Precision@5 ≥80%.
- [ ] Review the backend diff and update the approved TEST ledger with actual results.

## Task 7: Implement honest responsive and accessible frontend states

**Outcome IDs:** O1, O3, O4, O5, O8  
**Dependencies:** Task 1 and Task 6

**Files:**
- Modify: `apps/web/lib/types.ts`
- Modify: `apps/web/app/page.tsx`
- Modify: `apps/web/components/creator-card.tsx`
- Modify: `apps/web/components/score-breakdown.tsx`
- Modify: `apps/web/components/source-status.tsx`
- Modify: `apps/web/components/analysis-form.tsx`
- Modify: `apps/web/app/globals.css`

- [ ] Type `result_origin`, provenance, evidence score/availability, and stable API errors.
- [ ] Render a global LIVE/PROTOTYPE FIXTURE provenance indicator.
- [ ] Clear stale recommendations before a new request and on failed live analysis.
- [ ] Remove per-card synthetic/demo source copy.
- [ ] Render missing Engagement/Thailand/Style as `Not observed` with empty bars.
- [ ] Render unavailable LLM as `Unavailable` with an empty bar; never visually fill the neutral numeric fallback.
- [ ] Preserve rationale-before-details ordering and per-provider evidence status.
- [ ] Construct external TikTok URLs from validated usernames.
- [ ] Add labels, `aria-labelledby`, `aria-controls`, `aria-expanded`, `aria-busy`, status regions, alert regions, and visible focus states.
- [ ] Make Beta, creator rows, score rows, links, and provenance wrap or stack safely at 320px without changing desktop behavior.
- [ ] Run `npm --prefix apps/web run build` and `npm --prefix apps/web exec tsc -- --noEmit`.
- [ ] Verify with BrowserOS at 320px, 768px, 1024px, and 1440px: live failure shows no stale recommendations; explicit fixture response is labelled PROTOTYPE FIXTURE; unavailable evidence is visible; keyboard tab/enter/space behavior works; focus is visible; no horizontal overflow exists; console has no new errors.

**Acceptance:** The UI truthfully mirrors API availability/provenance and remains usable and accessible at all required widths.

## Task 8: Final documentation, ADR, runtime, and verification

**Outcome IDs:** O1–O9  
**Dependencies:** Checkpoint B and Task 7

**Files:**
- Create: `docs/decisions/ADR-001-truthful-live-provenance.md`
- Modify: `README.md`
- Modify: `kol-matcher-productionization_plan.md`
- Modify: `doc/instruction/PLAN.md`
- Modify: `doc/instruction/TEST.md`
- Modify: `doc/instruction/OUTCOME.md` only if verification reveals a genuine approved-requirement conflict

- [ ] Record the why behind fail-closed live behavior, explicit fixture origin, fixed incomplete scoring, no correctness caches, and evidence gates in the ADR.
- [ ] Update README and the root productionization plan so they no longer promise synthetic live fallback, neutral LLM ranking contribution, or `CACHED` fixture semantics.
- [ ] Replace the current PLAN summary with this approved plan and preserve execution evidence in TEST.
- [ ] Record every executed command, result, blocker, and residual risk in `doc/instruction/TEST.md`; never mark unrun checks as pass.
- [ ] Run `docker compose config --quiet`.
- [ ] Rebuild and start: `docker compose build --no-cache api web` followed by `docker compose up -d api web`.
- [ ] Verify API health, explicit fixture endpoint, deterministic matching endpoint, and live fail-closed behavior.
- [ ] Run `npm audit --omit=dev` and Docker `pip-audit --local`; record existing unresolved findings without forcing unrelated upgrades.
- [ ] Run `git diff --check` and inspect generated files, secrets, raw error leakage, stale `demo_pool`/`CACHED` references, and unintended artifacts.
- [ ] Perform final code review against O1–O9 and the decree.
- [ ] Request explicit user approval before any final atomic Git commit; stage only the approved allowlist.

**Acceptance:** Documentation, runtime, security, browser, backend, frontend, and benchmark evidence are fresh and traceable to O1–O9.

## Checkpoint C: Completion review

- [ ] All outcome IDs map to passing evidence or an explicitly recorded blocker.
- [ ] Full backend/evaluation suite passes.
- [ ] Benchmark thresholds pass.
- [ ] Frontend build/type-check passes.
- [ ] Docker rebuild/health/endpoints pass.
- [ ] Browser responsive/accessibility verification passes.
- [ ] Security and secret inspection passes.
- [ ] No unapproved files or generated artifacts remain.
- [ ] Final atomic commit is performed only after explicit approval.

## Rollback and Safeguards

- No database migration or irreversible data operation exists.
- Preserve the dirty worktree; never reset or clean unrelated changes.
- If a verification failure is caused by new work, revert only the affected task’s changes and tests, then rerun the relevant checkpoint.
- Do not restore synthetic live fallback, neutral LLM contribution, or `CACHED` fixture semantics to make tests pass.
- Keep live credentials out of fixtures, logs, browser URLs, frontend bundles, and artifacts.
- Keep Langflow outside `/api/analyze`; treat its Chat Output limitation as a separately documented blocker.
- Do not upgrade dependencies unless a separate approval changes the explicit exclusion.

## Final Allowlist

Only these paths may change under this plan:

- `apps/api/app/models/api.py`
- `apps/api/app/models/brand.py`
- `apps/api/app/models/evidence.py`
- `apps/api/app/models/creator.py`
- `apps/api/app/config.py`
- `apps/api/app/main.py`
- `apps/api/app/safety/url_safety.py`
- `apps/api/app/crawlers/facebook_crawler.py`
- `apps/api/app/crawlers/website_crawler.py`
- `apps/api/app/services/llm_client.py`
- `apps/api/app/services/llm_judge.py`
- `apps/api/app/services/brand_extractor.py`
- `apps/api/app/services/scorer.py`
- `apps/api/app/services/ranker.py`
- `apps/api/app/services/text_processing.py`
- `apps/api/app/services/bm25_matcher.py`
- `apps/api/app/services/pipeline.py`
- `apps/api/app/providers/base.py`
- `apps/api/app/providers/tiktok.py`
- `apps/api/app/providers/official_tiktok.py`
- `apps/api/app/providers/browser_tiktok.py`
- `apps/api/app/providers/tiktok_normalizer.py`
- `apps/api/app/providers/fixture_loader.py`
- `apps/api/tests/test_response_contract.py`
- `apps/api/tests/test_input_contract.py`
- `apps/api/tests/test_request_limits.py`
- `apps/api/tests/test_llm_client.py`
- `apps/api/tests/test_fixture_loader.py`
- `apps/api/tests/test_scorer.py`
- `apps/api/tests/test_ranking.py`
- `apps/api/tests/test_relevance_contract.py`
- `apps/api/tests/test_thai_processing.py`
- `apps/api/tests/test_tiktok_providers.py`
- `apps/api/tests/test_provider_provenance.py`
- `apps/api/tests/test_source_status.py`
- `apps/api/tests/test_live_fail_closed.py`
- `apps/api/tests/test_matching_api.py`
- `apps/api/tests/test_url_safety.py`
- `apps/api/tests/test_crawlers.py`
- `tests/evaluation/test_benchmark_brands.py`
- `apps/web/lib/types.ts`
- `apps/web/app/page.tsx`
- `apps/web/components/creator-card.tsx`
- `apps/web/components/score-breakdown.tsx`
- `apps/web/components/source-status.tsx`
- `apps/web/components/analysis-form.tsx`
- `apps/web/app/globals.css`
- `README.md`
- `kol-matcher-productionization_plan.md`
- `doc/instruction/OUTCOME.md`
- `doc/instruction/PLAN.md`
- `doc/instruction/TEST.md`
- `docs/decisions/ADR-001-truthful-live-provenance.md`
