"""Langflow adapter for the API's versioned KOL matcher."""
from __future__ import annotations

import json
from typing import Any

import httpx
from lfx.custom.custom_component.component import Component
from lfx.io import DropdownInput, MultilineInput, Output, StrInput
from lfx.schema import Data
from pydantic import BaseModel, Field, ValidationError


class _CandidateMatch(BaseModel):
    rank: int
    username: str
    normalized_score: float
    raw_score: float
    matched_keywords: list[str] = Field(default_factory=list)
    algorithm_key: str


class _MatchingResponse(BaseModel):
    algorithm_key: str
    matches: list[_CandidateMatch] = Field(default_factory=list)


class BM25MatcherComponent(Component):
    """Call the API matcher without duplicating ranking logic in Langflow."""

    display_name = "KOL BM25 Matcher"
    description = "Run the API's versioned KOL matching algorithm."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "waypoints"
    name = "KOLBM25Matcher"

    inputs = [
        MultilineInput(
            name="brand_profile_json",
            display_name="Brand Profile JSON",
            info="Serialized BrandProfile JSON accepted by the API.",
            value='{"brand_name":"Traveloka","topics":["travel"]}',
        ),
        MultilineInput(
            name="creators_json",
            display_name="Creators JSON",
            info="Serialized list of CreatorProfile objects accepted by the API.",
            value='[{"username":"travel.with.ink","bio":"travel creator","topic_tags":["travel"]}]',
        ),
        DropdownInput(
            name="algorithm_key",
            display_name="Algorithm",
            options=["bm25_v2_lekcut"],
            value="bm25_v2_lekcut",
        ),
        StrInput(
            name="api_url",
            display_name="Matcher API URL",
            value="http://api:8000/api/matching/score",
            advanced=True,
        ),
    ]

    outputs = [
        Output(
            name="matches",
            display_name="Matches",
            method="run_match",
        ),
    ]

    @staticmethod
    def _decode_json(value: str, label: str) -> Any:
        try:
            return json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{label} must contain valid JSON: {exc.msg}") from exc

    def run_match(self) -> Data:
        brand_profile = self._decode_json(self.brand_profile_json, "Brand Profile JSON")
        creators = self._decode_json(self.creators_json, "Creators JSON")
        if not isinstance(brand_profile, dict):
            raise ValueError("Brand Profile JSON must decode to an object")
        if not isinstance(creators, list):
            raise ValueError("Creators JSON must decode to an array")

        payload = {
            "brand_profile": brand_profile,
            "creators": creators,
            "algorithm_key": self.algorithm_key,
        }
        try:
            response = httpx.post(self.api_url, json=payload, timeout=60.0)
            response.raise_for_status()
            result = _MatchingResponse.model_validate(response.json())
        except httpx.HTTPError as exc:
            raise ValueError(f"Matcher API request failed: {exc}") from exc
        except (TypeError, ValidationError, ValueError) as exc:
            raise ValueError(f"Matcher API returned an invalid response: {exc}") from exc

        self.status = f"Matched {len(result.matches)} creators with {result.algorithm_key}."
        return Data(data=result.model_dump())
