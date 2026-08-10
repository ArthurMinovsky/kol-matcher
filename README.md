# Thai TikTok KOL Matcher

A deterministic KOL-ranking demo for Thai-market brands. Enter a **brand name**
and **Facebook page URL** (plus an optional website URL) and get an explainable
Top-15 list of TikTok creators scored on four factors.

No external API credentials are required for the deterministic **Dr. Pong**
demo.

## Quick Start

```bash
cp .env.example .env
docker compose up --build
```

Then open:

- Web UI: http://localhost:3000
- FastAPI docs: http://localhost:8000/docs

Click **Load Dr. Pong Demo**.

To stop: `docker compose down`

Ports are bound to `127.0.0.1` only. The web container waits for the API
healthcheck before starting.

## What this demonstrates

1. Structured brand intelligence from brand name + Facebook page URL.
2. Deterministic four-factor creator ranking.
3. Explicit evidence provenance and confidence.
4. Reproducible fixture-based operation without external services.
5. Optional live TikTok creator data via **Apify** when configured.
6. A polished evaluator-facing Next.js interface.

## Input contract

`POST /api/analyze`

```json
{
  "brand_name": "Dr. Pong Clinic",
  "facebook_url": "https://www.facebook.com/drpongclinic",
  "campaign_goal": "educational skincare",
  "website_url": "https://drpong.co.th"
}
```

- `brand_name` and `facebook_url` are required.
- `campaign_goal` is required and drives the **Style Fit** component.
- `website_url` is optional context for the LLM path.

## Architecture

```text
Brand name + FB URL (+ website)
        │
        ▼
┌─────────────────┐     ┌──────────────────┐
│ Dr. Pong match? │──YES──▶ Fixture pipeline │
└─────────────────┘     └──────────────────┘
        │ NO
        ▼
┌──────────────────┐
│ LLM available?   │──YES──▶ Typhoon → Gemini structured extraction
└──────────────────┘
        │ NO
        ▼
┌──────────────────┐
│ Heuristic        │──▶ Industry-keyword dictionary
│ brand profile    │
└──────────────────┘
        │
        ▼
┌──────────────────┐     ┌─────────────────┐
│ Apify available? │──YES──▶ Live TikTok   │
└──────────────────┘     │ creator search  │
        │ NO             └─────────────────┘
        ▼
┌──────────────────┐
│ Synthetic demo   │
│ pool (20 creators)
└──────────────────┘
        │
        ▼
Deterministic scoring → ranking → evidence → API → Next.js
```

## Deterministic ranking formula

```text
Match Score = 0.45 × Relevance
            + 0.25 × Engagement
            + 0.15 × Thailand Market Relevance
            + 0.15 × Style Fit
```

All components are clamped to `0..100`. Ranking uses unrounded values with a
deterministic tie-breaker:

```text
match_score DESC → relevance DESC → evidence_coverage DESC → username ASC
```

### Component details

- **Relevance**: cosine similarity between brand and creator embeddings for the
  Dr. Pong fixture; keyword-overlap fallback for general brands without
  embeddings.
- **Engagement**: median per-post rate of
  `(likes + 2×comments + 3×shares) / max(views, 1)`, clipped and pool-relative
  normalized.
- **Thailand Market Relevance**: observable content signals only
  (Thai caption ratio, Thai hashtags, Thai bio, Thailand location references).
  Never audience geography.
- **Style Fit**: overlap between campaign-goal style tags and creator style tags.

## Trust layer (independent of ranking)

- **Evidence Coverage**: measures information completeness (bio, posts,
  engagement, Thailand signals, metadata). Does not affect Match Score.
- **Audience Verification**: defaults to `Unavailable` because public TikTok
  data does not include demographics.
- **Recommendation Confidence**: `HIGH` / `MEDIUM` / `LOW` based on evidence
  coverage and match score. Does not affect ranking.

## Optional providers

| Provider | Env var | Purpose |
|----------|---------|---------|
| Typhoon (LLM) | `TYPHOON_API_KEY` | Structured brand profile extraction |
| Gemini (LLM) | `GEMINI_API_KEY` | Fallback LLM extraction |
| Apify (TikTok) | `APIFY_API_TOKEN` | Live TikTok creator discovery |

If no LLM key is provided, the system falls back to an industry-keyword
heuristic profile labelled as low-confidence.
If no Apify token is provided, the system ranks a committed mixed-industry
synthetic demo pool (20 creators) labelled as synthetic.

## Evaluation

The Dr. Pong fixture is evaluated with pairwise relevant-vs-irrelevant ordering
accuracy and Precision@5:

```bash
python -m tests.evaluation.evaluate
```

P0 thresholds:

- Pairwise accuracy ≥ 90%
- P@5 ≥ 80%

Run the full test suite:

```bash
cd apps/api
pytest tests -v
cd ../..
pytest tests/evaluation -v
```

## Native development (secondary)

Backend:

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend:

```bash
cd apps/web
npm install
npm run dev
```

## Fixture provenance

- `data/fixtures/drpong/` — 40 synthetic creators + brand profile for
  Dr. Pong Clinic. Pre-computed 16-dimensional embeddings are committed so the
  demo requires no OpenAI/Typhoon/Gemini embedding calls.
- `data/fixtures/demo_pool/` — 20 mixed-industry synthetic creators used as a
  fallback for general brands.

All synthetic data is explicitly labelled `source_type: synthetic` or
`source_type: cached` and surfaced as such in the UI.

## Limitations

- Live TikTok scraping is optional and gated behind Apify.
- No persistent database, authentication, or campaign management.
- General-brand relevance uses keyword overlap unless pre-computed embeddings
  are provided.
- Audience demographics are never assumed; verification is always
  `Unavailable`.

## Ethical constraints

- Synthetic/cached data is always labelled; missing metrics remain `None`.
- Thailand-market signals are distinguished from audience geography.
- Provider failures are visible in `source_status`; fallbacks never masquerade
  as live data.
- No secrets are committed (see `.gitignore`).

## License

MIT
