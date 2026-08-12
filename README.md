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

Click **Try Dr. Pong test case →** to fill the committed Dr. Pong inputs, then
submit the general analysis form.

To stop: `docker compose down`

Ports are bound to `127.0.0.1` only. The web container waits for the API
healthcheck before starting.

## What this demonstrates

1. Structured brand intelligence from brand name + Facebook page URL.
2. Deterministic four-factor creator ranking.
3. Explicit evidence provenance and confidence.
4. Reproducible BM25 matching over committed fixtures without model downloads.
5. Optional live TikTok creator data through the official Research API or an
   explicitly enabled browser provider.
6. Hybrid BM25 + LLM relevance with grounded brand and creator rationales.
7. A versioned `/api/matching/score` contract for algorithm experiments.
8. A polished evaluator-facing Next.js interface.

## Input contract

`POST /api/analyze`

```json
{
  "brand_name": "Dr. Pong Clinic",
  "facebook_url": "https://www.facebook.com/drpongclinic",
  "campaign_goal": "product review",
  "website_url": "https://drpong.co.th"
}
```

- `brand_name` and `facebook_url` are required.
- `campaign_goal` is required and drives the **Style Fit** component.
- `website_url` is optional context for brand-profile extraction.

## Architecture

```text
Brand name + FB URL (+ website)
        │
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
┌──────────────────────────┐     ┌─────────────────┐
│ Official API available?  │──YES──▶ Live TikTok   │
└──────────────────────────┘     │ creator search  │
        │ NO                     └─────────────────┘
        ▼
┌──────────────────────────┐     ┌─────────────────┐
│ Browser explicitly       │──YES──▶ Live TikTok   │
│ enabled?                 │        browser search │
└──────────────────────────┘     └─────────────────┘
        │ NO
        ▼
┌──────────────────────────┐
│ Synthetic demo pool      │
│ (20 creators, labelled)  │
└──────────────────────────┘
        │
        ▼
LEKCut → BM25 corpus matching → hybrid scoring → rationales → API → Next.js
```

The same deterministic matcher is exposed as `POST /api/matching/score` for
repeatable experiments. It accepts a validated `BrandProfile`, creator list,
and `algorithm_key` (`bm25_v2_lekcut`) and returns ordered raw/normalized scores
with observed matched terms. This endpoint remains deterministic and BM25-only.

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

- **Relevance**: a 45% composite of BM25 (20%) and an optional LLM judge (25%).
  The BM25 portion uses corpus-level `rank_bm25.BM25Okapi` over each creator's
  bio, captions, hashtags, topics, and raw text. The brand query combines
  structured Thai/English terms, products, campaign goal, and crawled text.
  Thai text is segmented with LEKCut's default DeepCut ONNX model; KeyBERT,
  embeddings, and sentence-transformer models are not used. Without LLM
  credentials, the judge is unavailable and contributes a neutral score of 50.
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
| TikTok Research API | `TIKTOK_RESEARCH_API_TOKEN` | Authorized live creator discovery |
| TikTok browser | `TIKTOK_BROWSER_ENABLED`, optional `TIKTOK_BROWSER_CDP_URL` | Explicit opt-in public-page fallback |
| Langflow lab | `LANGFLOW_SUPERUSER_PASSWORD` | Optional local algorithm orchestration |

If no LLM key is provided, the system falls back to an industry-keyword
heuristic profile labelled as low-confidence.
If no TikTok provider returns usable data, the system ranks a committed
mixed-industry demo pool labelled as synthetic. Browser collection is disabled
by default and does not use stealth patches, CAPTCHA solving, proxy rotation,
or other anti-bot bypasses.

### Optional Langflow matching laboratory

Langflow is not part of the default application path. Set
`LANGFLOW_SUPERUSER_PASSWORD` in `.env` (the default local username is
`langflow`), then run:

```bash
docker compose --profile matching-lab up --build
```

Open http://localhost:7860 and import
`langflow/flows/kol-bm25-evaluator.json`. The custom component calls the API's
`/api/matching/score` endpoint instead of reimplementing BM25. The component and
flow follow Langflow 1.11.x's documented custom-component and API patterns:

- https://docs.langflow.org/components-custom-components
- https://docs.langflow.org/api-reference-api-examples
- https://docs.langflow.org/deployment-docker

## Evaluation

The Dr. Pong, Parameter, and Traveloka cases are evaluated with deterministic
BM25 ranking. The benchmark uses pairwise relevant-vs-irrelevant ordering
accuracy and Precision@5:

```bash
PYTHONPATH=apps/api apps/api/.venv/bin/python tests/evaluation/evaluate.py
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
  Dr. Pong Clinic. The demo requires no model download or embedding service.
- `data/fixtures/demo_pool/` — 20 mixed-industry synthetic creators used as a
  fallback for general brands.

All synthetic data is explicitly labelled `source_type: synthetic` or
`source_type: cached` and surfaced as such in the UI.

## Limitations

- Live TikTok discovery is optional and gated behind authorized Research API
  access or explicit browser opt-in.
- No persistent database, authentication, or campaign management.
- BM25 quality depends on the lexical content available in structured profiles,
  crawled brand text, and creator bios/posts.
- Audience demographics are never assumed; verification is always
  `Unavailable`.

## Future Development

The following roadmap items are intentionally not part of the current
deterministic demo:

1. **Persistent data with SQLite.** Add a SQLite-backed data layer for brands,
   creators, campaigns, crawl runs, and matching history. This will make the
   project easier to scale beyond committed fixtures while keeping local
   development simple.
2. **Hybrid semantic retrieval.** Add Qdrant and the BGE-M3-RS embedding model
   for retrieval-augmented generation (RAG) and semantic creator search. BM25
   will remain available alongside vector retrieval so exact keywords and
   semantic similarity can complement each other.
3. **Structured crawler and ETL pipeline.** Replace ad-hoc collection paths
   with a custom crawler that has explicit extract, transform, and load stages,
   provenance, validation, scheduling, and repeatable crawl-run records.
4. **Private self-hosted model inference.** Replace third-party extraction API
   calls with a hosted Gemma 4 27B 3A model where appropriate, keeping brand
   and creator data inside the project-controlled inference environment.
5. **Configurable customer and KOL personas.** Add chat-configurable customer
   and creator personas, then include their goals, preferences, tone, and
   constraints in matching so recommendations can be tailored more directly.

## Ethical constraints

- Synthetic/cached data is always labelled; missing metrics remain `None`.
- Thailand-market signals are distinguished from audience geography.
- Provider failures are visible in `source_status`; fallbacks never masquerade
  as live data.
- Provider errors are sanitized and credentials/cookies are never logged.
- No secrets are committed (see `.gitignore`).

## License

Apache License 2.0. See [LICENSE](LICENSE).
