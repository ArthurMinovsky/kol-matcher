# Fix Typhoon and Deploy the Frontend to Vercel

## Summary

The target repository is on `main` with substantial pre-existing uncommitted work. Its current `apps/api/app/services/llm_client.py` performs a single non-streaming request using `settings.llm_config`, and `apps/api/app/config.py` still defaults Typhoon to `typhoon-v2.1-72b-instruct`. The frontend is a Next.js 14 app with `output: 'standalone'`, no `vercel.json`, and a legacy `next lint` script.

Fix only the Typhoon path in the target repository: use the supplied Typhoon model/base URL and robust OpenAI-compatible response handling. Use only Typhoon `typhoon-v2.5-30b-a3b-instruct`; do not configure or call Gemini. Then deploy only `apps/web` to Vercel, using the existing backend URL configuration if available. Do not touch Apify, Lightpanda, Playwright, Research API, Gemini, or unrelated pre-existing changes.

## Implementation

- Add a focused failing Typhoon client test under `apps/api/tests/` for the current target-repository contract: the Typhoon base URL/model selection, valid JSON extraction from the OpenAI-compatible response, and sanitized unavailable behavior after Typhoon failure.
- Update `apps/api/app/config.py` only as needed to set Typhoon’s default model to `typhoon-v2.5-30b-a3b-instruct` and preserve `https://api.opentyphoon.ai/v1`; do not change unrelated provider configuration.
- Update `apps/api/app/services/llm_client.py` only to make Typhoon behavior reliable: bounded timeout, response-shape validation, JSON/fenced-JSON parsing, and sanitized Typhoon failure. Do not print or log API keys, prompts, raw response bodies, or stack traces.
- Add or update only the minimum Python dependency/configuration required by the client and tests; do not refactor the provider system or alter TikTok provider ordering.
- Inspect the existing frontend API base URL handling and set the Vercel project root to `apps/web`; configure the production API URL as a Vercel environment variable if the repository already provides one. Do not deploy the Python API to Vercel unless the target runtime explicitly supports it.
- Run the frontend’s existing build/lint/type checks and fix only deployment-blocking issues in `apps/web`; leave unrelated backend/provider changes untouched.
- Deploy the frontend with the Vercel CLI or connected Vercel project, without committing secrets or writing the source `.env` into the repository.

## Verification

- Run the new focused Typhoon test red before changing the client, then green after the fix.
- Run the target API test suite relevant to the client and the frontend build/type/lint checks.
- Verify the deployed Vercel URL loads, the form renders, and the frontend makes requests to the configured API base URL rather than a local-only default.
- Verify Typhoon failures return sanitized unavailable behavior; do not call Gemini or require live response text in logs.
- Confirm no secret values, `.env` contents, raw upstream errors, or unrelated provider changes are present in the diff or deployment configuration.
- Run `git diff --check` and inspect final status, explicitly preserving all pre-existing uncommitted changes outside the Typhoon/deployment scope.

## Assumptions

- The existing Typhoon key is available through the target repository’s `.env` or deployment environment and will be passed only through environment configuration. Gemini is out of scope and must not be called.
- The Vercel project should deploy `apps/web` as the frontend only; the FastAPI backend remains hosted elsewhere and must be represented by a public API base URL.
- The user’s current deadline prioritizes a minimal verified Typhoon fix and frontend deployment over broader provider cleanup.
- No commit, branch reset, cleanup, or deletion of pre-existing work is authorized by this plan.
