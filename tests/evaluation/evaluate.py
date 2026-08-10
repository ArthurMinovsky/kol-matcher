"""Evaluation runner for Dr. Pong fixture."""
from __future__ import annotations

import asyncio
import json
import sys
from itertools import combinations
from pathlib import Path

# Allow running this script directly from the repo root.
_API_PATH = Path(__file__).parent.parent.parent / "apps" / "api"
if str(_API_PATH) not in sys.path:
    sys.path.insert(0, str(_API_PATH))

from app.models.brand import BrandProfile
from app.providers.fixture_loader import (
    inject_fixture_embeddings,
    load_drpong_creators,
    load_drpong_embeddings,
)
from app.services.ranker import score_and_rank


async def run_evaluation(top_n: int = 15):
    creators = load_drpong_creators()
    # Inject committed embeddings so relevance uses cosine similarity,
    # not the keyword-overlap fallback.
    inject_fixture_embeddings(creators)
    embeddings_data = load_drpong_embeddings()
    brand_embedding = embeddings_data.get("brand_embedding")
    fixture_dir = Path(__file__).parent.parent.parent / "data" / "fixtures" / "drpong"
    brand = BrandProfile.model_validate(
        json.load(open(fixture_dir / "brand_profile.json"))
    )
    recs = await score_and_rank(creators, brand, brand_embedding, top_n=40)
    ranked = [r.creator for r in recs]
    labels = {c.username: c.relevance_label for c in creators if c.relevance_label is not None}

    pair_correct = 0
    pair_total = 0
    for a, b in combinations(ranked, 2):
        la, lb = labels.get(a.username), labels.get(b.username)
        if la is None or lb is None:
            continue
        if la == 2 and lb == 0:
            pair_total += 1
            pair_correct += 1
        elif la == 0 and lb == 2:
            pair_total += 1

    acc = pair_correct / pair_total if pair_total else 0.0

    top5 = [labels[r.creator.username] for r in recs[:5] if r.creator.username in labels]
    p5 = sum(1 for l in top5 if l == 2) / 5

    print(f"Dr. Pong   Pairwise Accuracy: {acc:.2%}   P@5: {p5:.2%}")
    return {"pairwise_accuracy": acc, "precision_at_5": p5}


if __name__ == "__main__":
    asyncio.run(run_evaluation())
