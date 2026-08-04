import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bess_opt.kpi import classify, evaluate_kpis, relative_change_pct


def test_relative_change_uses_explicit_baseline():
    assert relative_change_pct(100.0, 113.0) == pytest.approx(13.0)


def test_kpis_are_computed_not_injected():
    metrics = evaluate_kpis(
        {"revenue": 100.0, "equivalent_cycles": 10.0, "runtime_seconds": 1380.0},
        {"revenue": 113.0, "equivalent_cycles": 8.6, "runtime_seconds": 480.0},
        {"maximum_deviation_pct": 1.4},
    )
    assert metrics["revenue_improvement_pct"] == pytest.approx(13.0)
    assert metrics["equivalent_cycle_reduction_pct"] == pytest.approx(14.0)
    assert metrics["baseline_runtime_minutes"] == pytest.approx(23.0)
    assert metrics["candidate_runtime_minutes"] == pytest.approx(8.0)


def test_missing_evidence_is_rejected():
    with pytest.raises(ValueError, match="Missing KPI evidence"):
        evaluate_kpis({}, {}, {})


def test_threshold_classification_reports_unmet_target():
    assert classify(12.0, 13.0, "at_least") == "Measured; target not met"
