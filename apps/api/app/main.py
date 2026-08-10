"""Thai TikTok KOL Matcher — FastAPI application."""
from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .models.api import AnalyzeRequest, AnalyzeResponse, HealthResponse
from .safety.url_safety import is_valid_facebook_url
from .services.pipeline import analyze_brand
from .services.ranker import run_fixture_pipeline

app = FastAPI(
    title="Thai TikTok KOL Matcher API",
    version="0.1.0",
    description=(
        "Deterministic KOL ranking for Thai TikTok creators. "
        "POST **/api/analyze** with brand name + Facebook URL, or click **GET /api/demo/drpong** "
        "to run the fixture demo without any credentials."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health ─────────────────────────────────────────────────────────────────

@app.get("/api/health", response_model=HealthResponse, tags=["ops"])
async def health() -> dict:
    """Health check used by Docker Compose and CI."""
    return {"status": "ok", "fixture_demo": True}


# ── Analyze endpoint ───────────────────────────────────────────────────────

@app.post(
    "/api/analyze",
    response_model=AnalyzeResponse,
    tags=["analyze"],
    summary="Analyze brand + find KOLs",
)
async def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    """Analyze a brand and return ranked TikTok KOL recommendations."""
    if not is_valid_facebook_url(req.facebook_url):
        raise HTTPException(
            status_code=400,
            detail="facebook_url must be a valid public facebook.com URL",
        )
    return await analyze_brand(req)


# ── Demo endpoint ──────────────────────────────────────────────────────────

@app.get(
    "/api/demo/drpong",
    response_model=AnalyzeResponse,
    tags=["demo"],
    summary="Dr. Pong Clinic — fixture demo",
    description=(
        "Runs the complete fixture pipeline: loads brand profile and 40 synthetic creators, "
        "scores each creator deterministically using the 45/25/15/15 weighting, "
        "and returns the top 15 ranked results. No API keys required."
    ),
)
async def demo_drpong(top_n: int = 15) -> AnalyzeResponse:
    """Return ranked KOL recommendations for the Dr. Pong Clinic demo.

    Args:
        top_n: Number of top recommendations to return (default 15, max 40).
    """
    if top_n < 1 or top_n > 40:
        raise HTTPException(status_code=400, detail="top_n must be between 1 and 40")
    try:
        return run_fixture_pipeline(top_n=top_n)
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Fixture data not found: {e}. Ensure data/fixtures/ is mounted.",
        ) from e
