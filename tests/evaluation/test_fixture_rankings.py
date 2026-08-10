"""Pytest wrapper for fixture evaluation."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

# Import evaluate.py from the same directory
_eval_path = Path(__file__).parent / "evaluate.py"
_spec = importlib.util.spec_from_file_location("evaluate", _eval_path)
_evaluate = importlib.util.module_from_spec(_spec)
# evaluate.py adds apps/api to sys.path when loaded, so app imports work
_evaluate.__file__ = str(_eval_path)
sys.modules["evaluate"] = _evaluate
_spec.loader.exec_module(_evaluate)
run_evaluation = _evaluate.run_evaluation


def test_drpong_evaluation_thresholds():
    metrics = run_evaluation()
    assert metrics["pairwise_accuracy"] >= 0.90
    assert metrics["precision_at_5"] >= 0.80
