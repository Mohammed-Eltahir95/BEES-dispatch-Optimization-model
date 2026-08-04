"""Evidence-driven KPI calculations; targets never influence model outputs."""
from __future__ import annotations

import math
from typing import Mapping


REQUIRED_SUMMARY_FIELDS = ("revenue", "equivalent_cycles", "runtime_seconds")


def _finite(summary: Mapping[str, float], field: str) -> float:
    if field not in summary:
        raise ValueError(f"Missing KPI evidence field: {field}")
    value = float(summary[field])
    if not math.isfinite(value):
        raise ValueError(f"KPI evidence field '{field}' must be finite.")
    return value


def relative_change_pct(baseline: float, candidate: float) -> float:
    """Return `(candidate - baseline) / abs(baseline) * 100`."""
    if not math.isfinite(baseline) or not math.isfinite(candidate) or baseline == 0:
        raise ValueError("Relative change requires finite values and non-zero baseline.")
    return 100.0 * (candidate - baseline) / abs(baseline)


def evaluate_kpis(
    baseline: Mapping[str, float],
    candidate: Mapping[str, float],
    validation: Mapping[str, float],
) -> dict[str, float]:
    """Calculate KPI values from separately generated evidence summaries."""
    for field in REQUIRED_SUMMARY_FIELDS:
        _finite(baseline, field)
        _finite(candidate, field)
    deviation = _finite(validation, "maximum_deviation_pct")
    return {
        "revenue_improvement_pct": relative_change_pct(
            float(baseline["revenue"]), float(candidate["revenue"])
        ),
        "equivalent_cycle_reduction_pct": -relative_change_pct(
            float(baseline["equivalent_cycles"]), float(candidate["equivalent_cycles"])
        ),
        "maximum_validation_deviation_pct": deviation,
        "baseline_runtime_minutes": float(baseline["runtime_seconds"]) / 60.0,
        "candidate_runtime_minutes": float(candidate["runtime_seconds"]) / 60.0,
    }


def classify(value: float, target: float, direction: str, tolerance: float = 1e-9) -> str:
    """Classify measured evidence against a declared threshold."""
    if direction == "at_least":
        return "Verified" if value + tolerance >= target else "Measured; target not met"
    if direction == "at_most":
        return "Verified" if value <= target + tolerance else "Measured; target not met"
    if direction == "approximately":
        return "Verified" if abs(value - target) <= tolerance else "Measured; target not met"
    raise ValueError(f"Unknown KPI direction: {direction}")
