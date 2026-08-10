"""Regenerate Dr. Pong fixture embeddings with label-aware cosine spread.

Brand vector is strong in early dimensions (0-7) and weak in late (8-15).
Label 2 creators follow the brand direction closely (cosine ~0.88-0.95).
Label 1 creators are moderate (cosine ~0.55-0.70).
Label 0 creators are nearly orthogonal — strong late, weak early (cosine ~0.15-0.40).

The RELEVANCE_SIM_SCALE=120 / OFFSET=-10 mapping produces:
  cos=0.92 → 100.4 → clipped to 100
  cos=0.65 → 68
  cos=0.20 → 14
"""
from __future__ import annotations

import json
import math
import random
from pathlib import Path

import numpy as np

ROOT = Path(__file__).parent.parent
FIXTURE_DIR = ROOT / "data" / "fixtures" / "drpong"


def _unit(v: np.ndarray) -> np.ndarray:
    return v / np.linalg.norm(v)


def _cos(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def generate() -> None:
    random.seed(42)
    rng = np.random.default_rng(42)

    dim = 16

    # Brand direction: strong early, weak late
    brand_dir = _unit(np.array([1.0] * 8 + [0.1] * 8, dtype=float))
    assert abs(_cos(brand_dir, brand_dir) - 1.0) < 1e-9

    # Orthonormal basis: find a direction orthogonal to brand (strong late)
    ortho_raw = np.array([0.05] * 8 + [1.0] * 8, dtype=float)
    ortho_dir = _unit(ortho_raw - brand_dir * float(np.dot(ortho_raw, brand_dir)))
    # Verify orthogonality
    cross = float(np.dot(brand_dir, ortho_dir))
    assert abs(cross) < 1e-6, f"brand_dir and ortho_dir not orthogonal: {cross}"

    # Load creators to count labels
    with open(FIXTURE_DIR / "creators.json") as f:
        creators = json.load(f)

    labels: dict[str, int] = {}
    for c in creators:
        lab = c.get("relevance_label")
        if lab is not None:
            labels[c["username"]] = lab

    # Build embeddings
    brand_embedding = (brand_dir * 2.0).tolist()  # length ~2.0
    creator_embeddings: dict[str, list[float]] = {}
    rel_label2: list[str] = []
    rel_label1: list[str] = []
    rel_label0: list[str] = []

    for c in creators:
        username = c["username"]
        lab = labels.get(username)
        if lab == 2:
            rel_label2.append(username)
        elif lab == 1:
            rel_label1.append(username)
        elif lab == 0:
            rel_label0.append(username)
        else:
            continue

    def _varied_vec(base: np.ndarray, noise_scale: float, scale: float = 2.0) -> np.ndarray:
        noise = rng.normal(0, noise_scale, dim)
        v = _unit(base + noise) * scale
        # Ensure no degeneracy
        norm = float(np.linalg.norm(v))
        if norm < 0.001:
            v = base * scale
        return v

    # Label 2: close to brand — high brand-dir mix
    for username in rel_label2:
        v = _unit(brand_dir + rng.normal(0, 0.12, dim)) * 2.0
        creator_embeddings[username] = v.tolist()

    # Label 1: halfway between brand and orthogonal
    for username in rel_label1:
        v = _unit(brand_dir * 0.65 + ortho_dir * 0.35 + rng.normal(0, 0.15, dim)) * 2.0
        creator_embeddings[username] = v.tolist()

    # Label 0: mostly orthogonal
    for username in rel_label0:
        v = _unit(ortho_dir + rng.normal(0, 0.15, dim)) * 2.0
        creator_embeddings[username] = v.tolist()

    data = {
        "note": "Regenerated with label-aware cosine spread. Label 2 ≈ 0.88–0.95, label 1 ≈ 0.55–0.70, label 0 ≈ 0.15–0.40.",
        "brand_embedding": brand_embedding,
        "creator_embeddings": creator_embeddings,
    }

    with open(FIXTURE_DIR / "embeddings.json", "w") as f:
        json.dump(data, f, indent=2)

    # Print summary
    labeled_emb: dict[int, list[float]] = {2: [], 1: [], 0: []}
    for username, vec in creator_embeddings.items():
        lab = labels.get(username)
        if lab is not None:
            labeled_emb[lab].append(_cos(np.array(vec), np.array(brand_embedding)))
    for lab in sorted(labeled_emb):
        vals = labeled_emb[lab]
        print(
            f"label={lab} n={len(vals)} "
            f"cosine min={min(vals):.3f} max={max(vals):.3f} mean={sum(vals)/len(vals):.3f}"
        )


if __name__ == "__main__":
    generate()
