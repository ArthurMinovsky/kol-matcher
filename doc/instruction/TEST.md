# TEST — Thai TikTok KOL Matcher (P0)

This file records every planned verification and its executed result. It is
derived from `OUTCOME.md` and `PLAN.md`; tests cite outcome IDs and plan tasks
explicitly.

Legend:
- **Outcome ID** — requirement from `OUTCOME.md`
- **Plan step** — task/risk in `PLAN.md`
- **Expected pass observation** — what must be true for the test to pass
- **Actual result** — updated during/after implementation

---

## T1 — Input contract validation

| | |
|---|---|
| **Outcome ID** | O1 |
| **Plan step** | Task 2: `AnalyzeRequest`; Task 12: route handler |
| **Rationale** | The API must reject malformed input before processing. |
| **Executable test/inspection** | `pytest apps/api/tests/test_api_request.py` (or POST to `/api/analyze` with invalid payloads) |
| **Expected pass observation** | Empty `brand_name`, non-http `facebook_url`, and non-http `website_url` each return 422/400 with clear errors. |
| **Actual result** | Not run |

---

## T2 — Facebook URL safety

| | |
|---|---|
| **Outcome ID** | O1 |
| **Plan step** | Task 3: `url_safety.py`; Task 12: endpoint guard |
| **Rationale** | Arbitrary URLs must not reach downstream providers. |
| **Executable test/inspection** | Unit test `is_valid_facebook_url`; POST `facebook_url=http://localhost/admin` → 400. |
| **Expected pass observation** | Localhost/private facebook URLs rejected; valid `facebook.com` URL accepted. |
| **Actual result** | Not run |

---

## T3 — Dr. Pong auto-route returns fixture

| | |
|---|---|
| **Outcome ID** | O2 |
| **Plan step** | Task 2: `is_drpong_request`; Task 12: `analyze_brand` |
| **Rationale** | Dr. Pong must work offline from committed fixtures. |
| **Executable test/inspection** | `POST /api/analyze {brand_name:"Dr. Pong", facebook_url:"https://www.facebook.com/drpongclinic", campaign_goal:"educational skincare"}` |
| **Expected pass observation** | Response has `source_status.brand_extraction == "CACHED"`, `source_status.tiktok == "CACHED"`, and identical Top 15 to `GET /api/demo/drpong`. |
| **Actual result** | Not run |

---

## T4 — Dr. Pong Top 15 default

| | |
|---|---|
| **Outcome ID** | O2 |
| **Plan step** | Task 11/12: default `top_n=15` |
| **Rationale** | Plan requires Top 15, not Top 10. |
| **Executable test/inspection** | `GET /api/demo/drpong` and inspect `recommendations` length. |
| **Expected pass observation** | Exactly 15 recommendations returned. |
| **Actual result** | Not run |

---

## T5 — Offline heuristic fallback path

| | |
|---|---|
| **Outcome ID** | O3 |
| **Plan step** | Task 5: `brand_heuristic.py`; Task 12: general pipeline |
| **Rationale** | General demo must work without API keys. |
| **Executable test/inspection** | With no `TYPHOON/GEMINI/APIFY` keys, POST a non-Dr. Pong brand. |
| **Expected pass observation** | `brand_profile.extraction_method == "heuristic"`, `limitations` contains "inferred from brand name only", and ranking uses demo pool labelled synthetic. |
| **Actual result** | Not run |

---

## T6 — LLM brand extraction when keys present

| | |
|---|---|
| **Outcome ID** | O4 |
| **Plan step** | Task 6: `llm_client.py`; Task 7: `brand_extractor.py` |
| **Rationale** | LLM path produces structured BrandProfile without touching ranking. |
| **Executable test/inspection** | Unit test with mocked `chat_json` returning valid JSON; or manual run with `TYPHOON_API_KEY` set. |
| **Expected pass observation** | `brand_profile.extraction_method == "llm"` and brand fields are populated; ranking still deterministic. |
| **Actual result** | Not run |

---

## T7 — Apify provider normalization and fallback

| | |
|---|---|
| **Outcome ID** | O5 |
| **Plan step** | Task 9: `providers/apify.py`; Task 12: fallback |
| **Rationale** | Apify is the priority live TikTok source; failures must fallback visibly. |
| **Executable test/inspection** | Unit test with mocked Apify API returning sample items; also test with mocked failure. |
| **Expected pass observation** | Success: items normalize to `CreatorProfile` with `source_type="live"` and `source_status.tiktok == "LIVE"`. Failure: `source_status.tiktok == "FAILED"` and response uses synthetic demo pool. |
| **Actual result** | Not run |

---

## T8 — Engagement scoring uses weighted median

| | |
|---|---|
| **Outcome ID** | O6 |
| **Plan step** | Task 10: `scorer.py` engagement update |
| **Rationale** | Engagement must follow the documented formula. |
| **Executable test/inspection** | `pytest apps/api/tests/test_scorer.py::test_engagement_uses_weighted_formula` |
| **Expected pass observation** | `(likes + 2*comments + 3*shares) / views` is verified, median is used, and pool-relative scaling works. |
| **Actual result** | Not run |

---

## T9 — Tie-breaker, deduplication, malformed skip

| | |
|---|---|
| **Outcome ID** | O6 |
| **Plan step** | Task 11: `ranker.py` |
| **Rationale** | Ranking must be deterministic and robust. |
| **Executable test/inspection** | `pytest apps/api/tests/test_ranking.py` |
| **Expected pass observation** | Top-N limits to N; duplicate usernames collapsed; malformed creators skipped without crash; tie resolved by relevance → coverage → username. |
| **Actual result** | Not run |

---

## T10 — Evidence coverage independent of Match Score

| | |
|---|---|
| **Outcome ID** | O7 |
| **Plan step** | Task 14: `test_evidence.py` |
| **Rationale** | Removing audience/bio metadata must not alter rank order. |
| **Executable test/inspection** | Compare rank order of a full creator vs the same creator with `bio=None`, `follower_count=None`. |
| **Expected pass observation** | Match Score unchanged; evidence coverage decreases; confidence may change. |
| **Actual result** | Not run |

---

## T11 — Prompt injection cannot reorder results

| | |
|---|---|
| **Outcome ID** | O4 / O7 |
| **Plan step** | Task 3: guarded prompt; Task 14: `test_prompt_safety.py` |
| **Rationale** | Untrusted input must not override deterministic ranking. |
| **Executable test/inspection** | `pytest apps/api/tests/test_prompt_safety.py` |
| **Expected pass observation** | A creator with injection text in bio/caption does not outrank a relevant creator purely because of the injection. |
| **Actual result** | Not run |

---

## T12 — Source status and provenance visibility

| | |
|---|---|
| **Outcome ID** | O5 / O7 |
| **Plan step** | Task 12: source_status mapping; Task 14: `test_source_status.py` |
| **Rationale** | Evaluator must see where each data element came from. |
| **Executable test/inspection** | `pytest apps/api/tests/test_source_status.py` |
| **Expected pass observation** | Fixture → CACHED; heuristic → CACHED/FAILED as designed; Apify failure → FAILED with demo pool fallback. |
| **Actual result** | Not run |

---

## T13 — Dr. Pong evaluation thresholds

| | |
|---|---|
| **Outcome ID** | O10 |
| **Plan step** | Task 15: `tests/evaluation/` |
| **Rationale** | Prove ranking behavior was deliberately checked. |
| **Executable test/inspection** | `python -m tests.evaluation.evaluate` and `pytest tests/evaluation/test_fixture_rankings.py` |
| **Expected pass observation** | Pairwise relevant > irrelevant accuracy ≥ 90%, P@5 ≥ 80%. |
| **Actual result** | Not run |

---

## T14 — Frontend build and centralized API client

| | |
|---|---|
| **Outcome ID** | O8 |
| **Plan step** | Task 16: `lib/api.ts`; Task 18: `page.tsx` |
| **Rationale** | Frontend must compile and not hardcode endpoints. |
| **Executable test/inspection** | `cd apps/web && npm install && npm run build`; grep for hardcoded `localhost:8000` outside `lib/api.ts`. |
| **Expected pass observation** | Build succeeds with 0 errors; no hardcoded API URLs in components. |
| **Actual result** | Not run |

---

## T15 — Docker Compose from clean checkout

| | |
|---|---|
| **Outcome ID** | O9 |
| **Plan step** | Task 1: env/compose; Task 21: final Docker verification |
| **Rationale** | Docker is the recommended evaluator path. |
| **Executable test/inspection** | `cp .env.example .env && docker compose build --no-cache && docker compose up` |
| **Expected pass observation** | Both images build; `curl http://localhost:8000/api/health` returns `{"status":"ok"}`; ports bound to 127.0.0.1 only. |
| **Actual result** | Not run |

---

## T16 — End-to-end evaluator journey

| | |
|---|---|
| **Outcome ID** | O8 / O9 / O10 |
| **Plan step** | Task 18/19: frontend; Task 21: final verification |
| **Rationale** | Validate the complete user path an evaluator will follow. |
| **Executable test/inspection** | With containers running, open `http://localhost:3000`; click **Load Dr. Pong Demo**. |
| **Expected pass observation** | Brand Intelligence panel visible; Top 15 list visible; each creator shows Match Score + 4 component scores; Evidence Coverage, Audience Verification, Confidence visible; source badges show CACHED. |
| **Actual result** | Not run |

---

## T17 — No secrets or transient artifacts committed

| | |
|---|---|
| **Outcome ID** | O9 (security) |
| **Plan step** | Task 20: `.gitignore`; Task 21: final atomic commit |
| **Rationale** | Secrets and local indexes must not enter git. |
| **Executable test/inspection** | `git status --short` before commit; inspect staged diff. |
| **Expected pass observation** | No `.env` files, `.codegraph/`, `node_modules/`, `__pycache__/`, or `.next/` staged. |
| **Actual result** | Not run |
