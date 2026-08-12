# Deploy Public FastAPI Backend on Vercel

## Summary

The frontend is deployed at `https://web-beta-six-97.vercel.app`, but it defaults to `http://localhost:8000`, so live analysis is not publicly reachable. The target FastAPI app exists at `apps/api/app/main.py`, depends on repository fixture data under `data/fixtures/`, and uses local-relative imports.

Deploy the backend as a separate Vercel Python project rooted at the repository root, add a minimal Vercel-compatible FastAPI entrypoint and dependency manifest, preserve current API routes, configure CORS for the deployed frontend, then set the frontend’s `NEXT_PUBLIC_API_BASE_URL` to the backend URL and redeploy the frontend. Do not alter Apify/browser-provider work.

## Implementation

- Add a root `api/index.py` Vercel entrypoint that adds `apps/api` to `sys.path` and exports `app` from `app.main`.
- Add a root `requirements.txt` derived from `apps/api/pyproject.toml` so Vercel installs the FastAPI runtime dependencies.
- Update `apps/api/app/main.py` only to make CORS accept the Vercel frontend origin via `CORS_ORIGINS`; preserve existing API routes, models, fixture behavior, and validation.
- Keep `data/fixtures/` in the backend deployment bundle and verify `/api/demo/drpong` can read it under Vercel’s read-only filesystem.
- Deploy the backend from the repository root with Vercel, creating a separate backend project.
- Set backend Vercel environment variables without exposing values:
  - `CORS_ORIGINS=https://web-beta-six-97.vercel.app`
  - `TYPHOON_API_KEY` from the existing target `.env`
  - Typhoon configuration only if required by the current backend.
- Verify backend `/api/health`, `/api/demo/drpong`, and `/docs`.
- Set `NEXT_PUBLIC_API_BASE_URL` on the existing Vercel frontend project to the new backend URL, redeploy it, and verify a frontend API request targets the public backend.
- Preserve all existing uncommitted work outside `api/index.py`, `requirements.txt`, CORS configuration, and Vercel deployment settings.

## Verification

- Run backend import/route checks locally before deployment.
- Verify the Vercel backend returns:
  - `200` from `/api/health`
  - `200` fixture data from `/api/demo/drpong`
  - accessible OpenAPI docs from `/docs`.
- Verify deployed frontend loads and no longer calls `localhost:8000`.
- Confirm CORS allows only the deployed frontend origin.
- Confirm no `.env` file, secret value, raw upstream failure, or unrelated code is uploaded or committed.
- Run `git diff --check` and inspect the final changed-file scope.

## Assumptions

- Vercel’s Python runtime supports this FastAPI bundle; its standard Python bundle limit is sufficient for the current dependencies and fixture data. [Vercel FastAPI documentation](https://vercel.com/docs/frameworks/backend/fastapi)
- The backend is deployed as a separate Vercel project because the frontend is already deployed from `apps/web`.
- The existing Vercel CLI login remains valid.
