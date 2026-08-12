"""Static contract checks for the optional Langflow matching laboratory."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).parents[2]
COMPONENT = ROOT / "langflow" / "components" / "kol_matching"
FLOW = ROOT / "langflow" / "flows" / "kol-bm25-evaluator.json"


def test_langflow_component_is_discoverable_and_api_backed():
    init_source = (COMPONENT / "__init__.py").read_text()
    component_source = (COMPONENT / "bm25_matcher_component.py").read_text()

    assert "BM25MatcherComponent" in init_source
    assert "LANGFLOW_COMPONENTS_PATH" not in component_source
    assert "/api/matching/score" in component_source
    assert "httpx" in component_source
    assert "BM25Okapi" not in component_source


def test_langflow_flow_contains_the_custom_matcher_node():
    flow = json.loads(FLOW.read_text())
    node_types = {
        node["data"]["node"]["type"]
        for node in flow["data"]["nodes"]
    }

    assert "KOLBM25Matcher" in node_types
    assert flow["data"]["edges"] == []
