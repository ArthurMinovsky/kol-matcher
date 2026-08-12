# Restore Availability-Aware Relevance Ranking

## Summary

The current implementation always feeds the unavailable LLM fallback score of `50` into the 45% relevance bucket. This gives every BM25-zero creator a neutral relevance of `27.78`, allowing high engagement or Thailand signals to outrank relevant creators. The full Docker suite reproduced this with `75 passed, 3 failed`; an in-memory control using BM25-only fallback restored cross-category Top-5 quality and Dr. Pong pairwise accuracy to `92.16%` with `80%` P@5.

Revise the approved plan so unavailable LLM evidence remains visibly `50` and marked unavailable, but ranking renormalizes the relevance bucket to the available BM25 signal. When the LLM is available, preserve the exact BM25 20% + LLM 25% formula. Preserve all completed LEKCut, provider, security, frontend, and documentation work.

## Implementation

- Update `apps/api/app/services/scorer.py` with an availability-aware relevance helper: use `(BM25 × 20 + LLM × 25) / 45` when the judge is available; use BM25 as the effective relevance when it is unavailable while retaining displayed LLM score `50`.
- Update `compute_match_score` and `apps/api/app/services/ranker.py` so `llm_available` propagates from `judge_result` into both `Recommendation.relevance` and final Match Score without changing the public response schema.
- Keep `compute_combined_relevance(bm25, llm)` behavior unchanged for the fully available hybrid contract and document the unavailable-signal renormalization in scoring evidence/rationale text.
- Add regression tests in `apps/api/tests/test_scorer.py`, `apps/api/tests/test_ranking.py`, and `apps/api/tests/test_relevance_contract.py` proving: available judges use both weights, unavailable judges retain neutral display evidence, BM25-zero creators cannot gain ranking relevance from the neutral fallback, and deterministic ranking remains stable.
- Re-run the existing benchmark tests in `tests/evaluation/test_benchmark_brands.py` and `tests/evaluation/test_fixture_rankings.py`; do not weaken thresholds or alter fixture labels.
- Update `kol-matcher-productionization_plan.md` and `doc/instruction/TEST.md` with the availability-aware fallback rule, the reproduced failure, the control result, and the final validation evidence.
- Preserve the current dirty worktree and completed changes; do not reset, regenerate embeddings, restore removed dependencies, or introduce unrelated refactors.
- If the amended scoring behavior fails verification, revert only the new scorer/ranker fallback hunks and their regression tests while keeping the LEKCut/provider/UI work intact.

## Verification

- Run focused Docker tests for scorer, ranker, relevance contract, tokenizer, BM25, API, URL safety, crawlers, providers, and source status; expect zero failures.
- Run `PYTHONPATH=/workspace/apps/api pytest apps/api/tests tests/evaluation -q` in the Python 3.12 Docker image; require all tests to pass.
- Run the Dr. Pong evaluator and confirm pairwise accuracy ≥90% and Precision@5 ≥80%.
- Confirm benchmark Top-5 results contain at least 80% relevant creators for Dr. Pong, Parameter, and Traveloka.
- Confirm available-LLM tests still report the exact 20% BM25/25% LLM relevance weights and unavailable-LLM responses show `50` with `available=false`.
- Re-run `npm run build` and `npx tsc --noEmit`; validate Compose configuration and health checks.
- Re-run browser verification for the unchanged Dr. Pong autofill flow, rationale placement, score labels, provenance, accessibility tree, network behavior, and console output.
- Run `npm audit --omit=dev` and `pip-audit`; inspect final stale-reference, secret, cache, and generated-artifact state.
- Record the final results and any remaining lint/Langflow blockers in `doc/instruction/TEST.md`.

## Assumptions

- The user-approved `campaign_goal`, LEKCut `bm25_v2_lekcut`, provider order, browser opt-in policy, and score weights remain unchanged.
- “Neutral LLM fallback score 50” means the evidence value remains 50 and unavailable, not that unavailable evidence should influence ordering.
- With a real judge result, the existing hybrid formula and rationale behavior remain unchanged.
- The authoritative plan artifact remains `/Users/aminovsky/Desktop/Personal/Code_project/Engineering/kol-matcher/kol-matcher-productionization_plan.md`.
- Python 3.12 Docker remains the reproducible backend verification environment because the local Python 3.14 virtual environment lacks LEKCut.
- No external TikTok credentials are required for the fallback regression tests.

## Execution Evidence

- The original regression reproduced as `75 passed, 3 failed`; the failure was
  traced to unavailable LLM score `50` being included in effective relevance.
- The availability-aware scorer/ranker implementation and regression tests now
  pass: focused suite `43 passed`; full backend/evaluation suite `82 passed`.
- Standalone Dr. Pong evaluation reports pairwise accuracy `92.16%` and P@5
  `80.00%`.
- Frontend build/type-check, Compose configuration, container health, API
  health, browser verification, stale-reference inspection, and diff checks
  passed.
- `pip-audit` found no known vulnerabilities apart from skipping the local
  non-PyPI `kol-api` package. `npm audit --omit=dev` remains an open blocker
  with one critical and one high issue in the existing Next/PostCSS chain;
  dependency upgrades were intentionally not included in this scoring fix.
