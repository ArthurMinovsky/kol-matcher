# TEST — Truthful Prototype-Ready KOL Matcher Verification Ledger

## Verification Status

- Status: Planned; implementation has not started.
- Every new case below starts as `Not run`.
- A case may be marked `Pass` only after its command or browser evidence is captured.
- Historical results are retained for context but do not prove the new fail-closed, evidence-gated contract.

## Verification Environment

- Repository: `/Users/aminovsky/Desktop/Personal/Code_project/Engineering/kol-matcher`
- Backend runtime: Python 3.12 Docker API image.
- Frontend runtime: Next.js application in `apps/web`.
- Browser verification: BrowserOS.
- Reproducible backend command prefix: `docker compose run --rm api sh -lc 'PYTHONPATH=/workspace/apps/api ...'`

## Planned Test Cases

### TC-001 — API provenance and evidence contract

**Traceability:** O1, O3, O4, O5, O7; PLAN Task 1  
**Risk covered:** API and frontend can disagree about live, fixture, or unavailable evidence state.  
**Test code path:** `apps/api/tests/test_response_contract.py`, `apps/api/tests/test_input_contract.py`  
**Verification:**

```bash
docker compose run --rm api sh -lc 'PYTHONPATH=/workspace/apps/api pytest apps/api/tests/test_response_contract.py apps/api/tests/test_input_contract.py -q'
```

**Expected pass observation:**

- `LIVE` and `PROTOTYPE_FIXTURE` are accepted as distinct result origins.
- Evidence exposes numeric score, availability, and display state.
- Required input remains present and bounded.
- Stable sanitized error shape contains a machine code and no raw internals.

**Actual:** Not run.

### TC-002 — Input bounds and early rejection

**Traceability:** O7; PLAN Tasks 1–2  
**Risk covered:** Oversized or malformed requests reach expensive providers.  
**Test code path:** `apps/api/tests/test_input_contract.py`, `apps/api/tests/test_request_limits.py`  
**Verification:**

```bash
docker compose run --rm api sh -lc 'PYTHONPATH=/workspace/apps/api pytest apps/api/tests/test_input_contract.py apps/api/tests/test_request_limits.py -q'
```

**Expected pass observation:**

- Empty/oversized fields and nested collections are rejected before provider calls.
- Unexpected fields are rejected where the contract requires strict input.
- Rate-limited requests return sanitized `429` and do not invoke providers.

**Actual:** Not run.

### TC-003 — DNS and URL SSRF protection

**Traceability:** O7; PLAN Task 2  
**Risk covered:** DNS rebinding, private-IP access, credential-bearing URLs, and alternate IP forms.  
**Test code path:** `apps/api/tests/test_url_safety.py`  
**Verification:**

```bash
docker compose run --rm api sh -lc 'PYTHONPATH=/workspace/apps/api pytest apps/api/tests/test_url_safety.py -q'
```

**Expected pass observation:**

- Loopback, private, link-local, reserved, multicast, IPv4-mapped IPv6, and numeric private targets are rejected.
- Credential-bearing and non-HTTPS targets are rejected.
- Valid configured public URLs remain accepted.
- No crawler call occurs after rejection.

**Actual:** Not run.

### TC-004 — Redirect and response-size safety

**Traceability:** O7; PLAN Task 2  
**Risk covered:** A validated public URL redirects to a private host or returns an unbounded body.  
**Test code path:** `apps/api/tests/test_crawlers.py`, `apps/api/tests/test_url_safety.py`  
**Verification:**

```bash
docker compose run --rm api sh -lc 'PYTHONPATH=/workspace/apps/api pytest apps/api/tests/test_crawlers.py apps/api/tests/test_url_safety.py -q'
```

**Expected pass observation:**

- Every redirect destination is revalidated.
- Redirects to private, credential-bearing, disallowed, or unsafe targets fail closed.
- Oversized and non-HTML responses are rejected or bounded.
- Crawler errors are sanitized.

**Actual:** Not run.

### TC-005 — CORS normalization and error sanitization

**Traceability:** O3, O7; PLAN Task 2  
**Risk covered:** Wildcard/whitespace CORS configuration and internal error disclosure.  
**Test code path:** `apps/api/tests/test_request_limits.py`, API integration assertions  
**Verification:**

```bash
docker compose run --rm api sh -lc 'PYTHONPATH=/workspace/apps/api pytest apps/api/tests/test_request_limits.py -q'
```

Manual/API checks:

- Send preflight from an allowed normalized origin.
- Send preflight from an unlisted origin.
- Trigger fixture failure and provider failure.

**Expected pass observation:**

- Allowed origins are trimmed, normalized, deduplicated, and accepted.
- Unlisted origins and wildcard configuration are denied.
- Responses expose no filesystem paths, stack traces, tokens, cookies, prompts, or upstream response bodies.

**Actual:** Not run.

### TC-006 — Request deadline and cleanup

**Traceability:** O3, O7; PLAN Task 2  
**Risk covered:** Slow providers or browser work outlive the request and consume resources.  
**Test code path:** `apps/api/tests/test_request_limits.py`, provider cleanup assertions  
**Verification:**

```bash
docker compose run --rm api sh -lc 'PYTHONPATH=/workspace/apps/api pytest apps/api/tests/test_request_limits.py -q'
```

**Expected pass observation:**

- Analysis terminates at the configured 60-second deadline.
- Pending provider/model/browser tasks are cancelled.
- Browser contexts and HTTP clients are closed.
- The API returns sanitized `REQUEST_DEADLINE_EXCEEDED` with zero recommendations.

**Actual:** Not run.

### TC-007 — Typhoon-to-Gemini failover

**Traceability:** O4, O6; PLAN Task 3  
**Risk covered:** Typhoon failure silently becomes heuristic/neutral output without trying Gemini.  
**Test code path:** `apps/api/tests/test_llm_client.py`  
**Verification:**

```bash
docker compose run --rm api sh -lc 'PYTHONPATH=/workspace/apps/api pytest apps/api/tests/test_llm_client.py -q'
```

**Expected pass observation:**

- Typhoon is attempted first.
- Gemini is attempted once after Typhoon timeout, rate limit, upstream failure, malformed JSON, or schema-invalid output.
- Both-provider failure becomes sanitized unavailable output.
- Provider order and outcomes appear in provenance.
- Tokens and raw provider URLs never appear in logs or responses.

**Actual:** Not run.

### TC-008 — LLM schema validation and cache isolation

**Traceability:** O4, O6; PLAN Task 3  
**Risk covered:** Invalid model output or stale process-global failures affect later requests.  
**Test code path:** `apps/api/tests/test_llm_client.py`, `apps/api/tests/test_relevance_contract.py`, `apps/api/tests/test_fixture_loader.py`  
**Verification:**

```bash
docker compose run --rm api sh -lc 'PYTHONPATH=/workspace/apps/api pytest apps/api/tests/test_llm_client.py apps/api/tests/test_relevance_contract.py apps/api/tests/test_fixture_loader.py -q'
```

**Expected pass observation:**

- Extra/malformed model fields are rejected.
- Unavailable judge evidence is score `0`, `available=false`, and truthful.
- A failed request does not poison a later successful request.
- Mutating one loaded fixture does not mutate the next request’s fixture.
- No `_judge_cache` or fixture-loader `lru_cache` remains in correctness paths.

**Actual:** Not run.

### TC-009 — Exact available/unavailable scoring

**Traceability:** O4; PLAN Task 4  
**Risk covered:** Missing LLM evidence is renormalized or rendered as an authoritative score.  
**Test code path:** `apps/api/tests/test_scorer.py`, `apps/api/tests/test_ranking.py`, `apps/api/tests/test_relevance_contract.py`  
**Verification:**

```bash
docker compose run --rm api sh -lc 'PYTHONPATH=/workspace/apps/api pytest apps/api/tests/test_scorer.py apps/api/tests/test_ranking.py apps/api/tests/test_relevance_contract.py -q'
```

**Expected pass observation:**

- Available mode uses BM25 20% + LLM 25% + Engagement 25% + Thailand 15% + Style 15%.
- Unavailable mode contributes BM25 20% and LLM 0%.
- The missing 25% is not renormalized.
- Deterministic ordering remains stable.
- A BM25-zero creator gains no relevance from an unavailable LLM fallback.

**Actual:** Not run.

### TC-010 — Engagement, Thailand, and Style availability

**Traceability:** O5; PLAN Task 4  
**Risk covered:** Missing metrics become fabricated scores or false evidence.  
**Test code path:** `apps/api/tests/test_scorer.py`, `apps/api/tests/test_ranking.py`  
**Verification:**

```bash
docker compose run --rm api sh -lc 'PYTHONPATH=/workspace/apps/api pytest apps/api/tests/test_scorer.py apps/api/tests/test_ranking.py -q'
```

**Expected pass observation:**

- Engagement uses valid recent post metrics and weighted median.
- Follower-only creators do not receive engagement fallback.
- Missing Engagement, Thailand, or Style is score `0`, `available=false`, and `Not observed`.
- `has_thailand_location` is included correctly.
- Observable Thailand signals never become audience-geography claims.
- Explicit brand no-style-preference can receive the permitted neutral style state.

**Actual:** Not run.

### TC-011 — Thai low-signal matching regressions

**Traceability:** O5, O9; PLAN Task 4  
**Risk covered:** Low-signal Thai variants create false relevance or regress LEKCut behavior.  
**Test code path:** `apps/api/tests/test_thai_processing.py`, matcher tests  
**Verification:**

```bash
docker compose run --rm api sh -lc 'PYTHONPATH=/workspace/apps/api pytest apps/api/tests/test_thai_processing.py -q'
```

**Expected pass observation:**

- `ง่าย`, `ง่ายๆ`, `ทำง่าย`, and `easy` are treated consistently.
- `bm25_v2_lekcut` remains the active algorithm key.
- Existing meaningful Thai terms remain matchable.
- Stable tie-breaking is preserved.

**Actual:** Not run.

### TC-012 — Official provider ordering and malformed records

**Traceability:** O1, O2, O3; PLAN Task 5  
**Risk covered:** Browser is used before official data, malformed records pass, or provenance is lost.  
**Test code path:** `apps/api/tests/test_tiktok_providers.py`, `apps/api/tests/test_provider_provenance.py`  
**Verification:**

```bash
docker compose run --rm api sh -lc 'PYTHONPATH=/workspace/apps/api pytest apps/api/tests/test_tiktok_providers.py apps/api/tests/test_provider_provenance.py -q'
```

**Expected pass observation:**

- Official provider is attempted first.
- Browser fallback is attempted only after official failure/unavailability.
- Malformed records are skipped and counted.
- Creator/post caps and deduplication are enforced.
- Attempt order, status, counts, and capture time are returned without secrets.

**Actual:** Not run.

### TC-013 — Three-caption minimum evidence

**Traceability:** O1, O2; PLAN Task 5  
**Risk covered:** Profile-only, hashtag-only, or insufficient records become live recommendations.  
**Test code path:** `apps/api/tests/test_tiktok_providers.py`  
**Verification:**

```bash
docker compose run --rm api sh -lc 'PYTHONPATH=/workspace/apps/api pytest apps/api/tests/test_tiktok_providers.py -q'
```

**Expected pass observation:**

- Zero, one, or two usable captions reject the creator.
- Hashtag-only captions do not count.
- Duplicate posts do not count twice.
- Exactly three distinct recent usable captions accept the creator.
- Malicious external `href` values are discarded; constructed TikTok URLs are used.

**Actual:** Not run.

### TC-014 — Browser provider evidence collection

**Traceability:** O1, O2, O3; PLAN Task 5  
**Risk covered:** Browser fallback returns only visible profile links.  
**Test code path:** `apps/api/tests/test_tiktok_providers.py`, browser provider fixtures  
**Verification:**

```bash
docker compose run --rm api sh -lc 'PYTHONPATH=/workspace/apps/api pytest apps/api/tests/test_tiktok_providers.py -q'
```

**Expected pass observation:**

- Browser provider remains opt-in and public-only.
- Each accepted browser creator includes canonical profile evidence and three captioned recent posts.
- Browser navigation and evidence collection are bounded.
- No stealth, CAPTCHA, proxy, or access-control bypass behavior is introduced.

**Actual:** Not run.

### TC-015 — Live fail-closed pipeline

**Traceability:** O1, O3; PLAN Task 6  
**Risk covered:** Provider failure silently returns synthetic creators.  
**Test code path:** `apps/api/tests/test_live_fail_closed.py`, `apps/api/tests/test_source_status.py`  
**Verification:**

```bash
docker compose run --rm api sh -lc 'PYTHONPATH=/workspace/apps/api pytest apps/api/tests/test_live_fail_closed.py apps/api/tests/test_source_status.py -q'
```

**Expected pass observation:**

- Official failure plus browser failure returns sanitized `503`/`504`.
- Zero accepted creators returns zero recommendations.
- No live call loads `load_demo_pool_creators`.
- Live failure provenance never says `LIVE` or `PROTOTYPE_FIXTURE` for recommendations because no recommendations exist.
- Existing tests no longer assert demo-pool fallback.

**Actual:** Not run.

### TC-016 — Explicit fixture and matching-lab behavior

**Traceability:** O1, O9; PLAN Task 6  
**Risk covered:** Removing live fallback breaks deterministic offline evaluation.  
**Test code path:** `apps/api/tests/test_matching_api.py`, fixture tests, evaluation tests  
**Verification:**

```bash
docker compose run --rm api sh -lc 'PYTHONPATH=/workspace/apps/api pytest apps/api/tests/test_matching_api.py tests/evaluation/test_benchmark_brands.py tests/evaluation/test_fixture_rankings.py -q'
```

**Expected pass observation:**

- `/api/demo/drpong` remains credential-free and deterministic.
- Fixture results use `PROTOTYPE_FIXTURE`, never `CACHED`.
- Missing/invalid fixtures return sanitized errors without filesystem paths.
- `/api/matching/score` remains BM25-only and deterministic.
- Benchmark thresholds remain pairwise accuracy ≥90% and Precision@5 ≥80%.

**Actual:** Not run.

### TC-017 — Frontend availability and stale-result handling

**Traceability:** O1, O3, O4, O5, O8; PLAN Task 7  
**Risk covered:** UI displays stale or fabricated data after live failure.  
**Test code path:** BrowserOS manual verification; no frontend test runner currently exists.  
**Verification:**

1. Submit a live request with providers unavailable.
2. Confirm existing recommendations clear before/when the error appears.
3. Load the explicit Dr. Pong fixture path.
4. Inspect provenance, score rows, unavailable evidence, and rationale order.

**Expected pass observation:**

- Live failure shows an actionable sanitized error and no stale recommendations.
- Fixture result shows `PROTOTYPE FIXTURE`.
- Missing factors show `Not observed`.
- Unavailable LLM shows `Unavailable` with an empty bar.
- No per-card synthetic/demo source label appears.

**Actual:** Not run.

### TC-018 — Responsive and accessibility behavior

**Traceability:** O8; PLAN Task 7  
**Risk covered:** Small screens, keyboard users, and assistive technologies cannot use or interpret the result.  
**Test code path:** BrowserOS at 320px, 768px, 1024px, and 1440px.  
**Verification:**

- Use viewport widths 320, 768, 1024, and 1440.
- Tab through form controls, creator toggles, links, and score details.
- Activate creator toggles with Enter and Space.
- Inspect focus indicators and accessibility tree.
- Trigger loading and error states.

**Expected pass observation:**

- No horizontal overflow.
- Beta pill, creator rows, score rows, links, and provenance remain visible.
- Labels and headings are associated.
- Expanded/collapsed state and controlled regions are announced.
- Loading uses a status region; errors use an alert region.
- Focus is visible and not clipped.

**Actual:** Not run.

### TC-019 — Frontend build and type contract

**Traceability:** O1, O4, O5, O8; PLAN Task 7  
**Risk covered:** Backend contract changes break the web build or create unsafe implicit types.  
**Test code path:** `apps/web/lib/types.ts`, TypeScript compiler, Next build  
**Verification:**

```bash
npm --prefix apps/web run build
npm --prefix apps/web exec tsc -- --noEmit
```

**Expected pass observation:**

- Production build succeeds.
- TypeScript reports no errors.
- Result origin, provenance, evidence availability, and stable errors are typed.

**Actual:** Not run.

### TC-020 — Docker/runtime endpoints

**Traceability:** O9; PLAN Task 8  
**Risk covered:** Runtime changes break local startup or deterministic endpoints.  
**Test code path:** Docker Compose and API endpoints  
**Verification:**

```bash
docker compose config --quiet
```

Then verify:

- `GET /api/health`
- `GET /api/demo/drpong?top_n=15`
- `POST /api/matching/score`
- live `/api/analyze` failure with providers unavailable

**Expected pass observation:**

- API and web containers start with optional credentials absent.
- API health is successful.
- Fixture and matching endpoints remain deterministic.
- Live analysis terminates with sanitized failure and zero recommendations.
- Ports remain loopback-bound.

**Actual:** Not run.

### TC-021 — Full backend/evaluation regression

**Traceability:** O1–O9; PLAN Checkpoint B  
**Risk covered:** Focused fixes regress unrelated ranking, provider, crawler, or benchmark behavior.  
**Test code path:** `apps/api/tests`, `tests/evaluation`  
**Verification:**

```bash
docker compose run --rm api sh -lc 'PYTHONPATH=/workspace/apps/api pytest apps/api/tests tests/evaluation -q'
python tests/evaluation/evaluate.py
```

**Expected pass observation:**

- Full backend/evaluation suite passes.
- Pairwise accuracy is at least 90%.
- Precision@5 is at least 80%.
- No threshold is weakened to accommodate the implementation.

**Actual:** Not run.

### TC-022 — Security and dependency inspection

**Traceability:** O3, O7, O9; PLAN Task 8  
**Risk covered:** Secret leakage, unsafe generated artifacts, and unreported dependency/runtime risk.  
**Test code path:** repository inspection, audit tools, Docker image  
**Verification:**

```bash
npm audit --omit=dev
```

Also inspect:

- response bodies and logs for tokens, cookies, prompts, paths, and raw exceptions;
- stale `demo_pool`/`CACHED` references;
- generated files and unexpected artifacts;
- provider URLs and frontend bundles for secrets.

**Expected pass observation:**

- No new critical security issue is introduced by this work.
- No secret or raw internal error is present.
- Existing audit/Langflow blockers are explicitly recorded if unresolved.
- Diff has no whitespace errors or unapproved generated artifacts.

**Actual:** Not run.

## Historical Baseline — Not Acceptance Evidence for This Revision

The following results predate the approved fail-closed and fixed-incomplete-scoring outcome:

- Focused backend relevance suite: `43 passed`.
- Full backend/evaluation suite: `82 passed`.
- Dr. Pong evaluator: pairwise accuracy `92.16%`; Precision@5 `80.00%`.
- Frontend build/type-check: previously passed.
- Docker Compose health and prior browser flow: previously passed.
- Prior general `/api/analyze` verification used synthetic fallback and therefore must be replaced by TC-015/TC-020 evidence.
- `npm audit --omit=dev`: previously reported one critical and one high issue in the existing Next/PostCSS chain.
- Langflow CLI: previously blocked by missing Chat Output.
- Live TikTok credential verification: not previously executed.

## Outcome-to-Test Mapping

| Outcome | Required tests |
|---|---|
| O1 | TC-001, TC-012, TC-013, TC-015, TC-016, TC-017, TC-020 |
| O2 | TC-012, TC-013, TC-014 |
| O3 | TC-001, TC-005, TC-006, TC-008, TC-012, TC-015, TC-017, TC-022 |
| O4 | TC-001, TC-007, TC-008, TC-009, TC-017, TC-019 |
| O5 | TC-001, TC-010, TC-011, TC-017, TC-019 |
| O6 | TC-007, TC-008, TC-012 |
| O7 | TC-001, TC-002, TC-003, TC-004, TC-005, TC-006, TC-022 |
| O8 | TC-017, TC-018, TC-019 |
| O9 | TC-011, TC-016, TC-020, TC-021 |

## Residual Risks

- Live-provider behavior cannot be fully verified without valid credentials.
- Existing npm audit findings may remain because unrelated dependency upgrades are excluded.
- Langflow remains a separate laboratory limitation when its flow lacks Chat Output.
- Browser/CDP behavior may vary by installed runtime; bounded failure is required even when live success cannot be exercised.
