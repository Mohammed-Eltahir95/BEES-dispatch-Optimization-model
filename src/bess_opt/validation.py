"""Scientific input and solution checks independent of the optimizer rules."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
import math

import pandas as pd
import pyomo.environ as pyo


def validate_inputs(
    time_index: Sequence[datetime],
    market_prices: Mapping[str, pd.Series],
    params: Mapping[str, float],
) -> None:
    """Raise ``ValueError`` when model inputs violate units or core assumptions."""
    if not time_index:
        raise ValueError("Optimization horizon must contain at least one timestamp.")
    index = pd.DatetimeIndex(time_index)
    if index.has_duplicates or not index.is_monotonic_increasing:
        raise ValueError("Timestamps must be unique and strictly increasing.")
    if len(index) > 2:
        steps = index.to_series().diff().dropna()
        if steps.nunique() != 1 or steps.iloc[0] <= pd.Timedelta(0):
            raise ValueError("Timestamps must use a positive, constant interval.")

    if not market_prices:
        raise ValueError("At least one enabled market-price series is required.")
    for market, series in market_prices.items():
        aligned = series.reindex(index)
        if aligned.isna().any() or not aligned.map(math.isfinite).all():
            raise ValueError(f"Market '{market}' has missing or non-finite horizon prices.")

    positive = ("battery.energy_capacity_mwh", "battery.power_limit_mw")
    for key in positive:
        if float(params.get(key, 0.0)) <= 0:
            raise ValueError(f"{key} must be positive.")
    fractions = (
        "battery.charge_efficiency", "battery.discharge_efficiency",
        "battery.soc_min_pct", "battery.soc_max_pct",
        "battery.soc_initial_pct", "battery.soc_final_pct",
    )
    for key in fractions:
        value = float(params.get(key, float("nan")))
        if not 0.0 <= value <= 1.0 or not math.isfinite(value):
            raise ValueError(f"{key} must be a finite fraction in [0, 1].")
    soc_min = float(params["battery.soc_min_pct"])
    soc_max = float(params["battery.soc_max_pct"])
    for key in ("battery.soc_initial_pct", "battery.soc_final_pct"):
        if not soc_min <= float(params[key]) <= soc_max:
            raise ValueError(f"{key} must lie within configured SOC bounds.")


def validate_solution(model: pyo.ConcreteModel, tolerance: float = 1e-6) -> dict[str, float]:
    """Check physical constraints from solved values and return max residuals."""
    max_energy_residual = 0.0
    max_power_violation = 0.0
    capacity = pyo.value(model.E_capacity)
    previous_soc = pyo.value(model.soc_initial) * capacity
    for t in model.T:
        charge = sum(pyo.value(model.charge[t, m]) for m in model.MARKETS)
        discharge = sum(pyo.value(model.discharge[t, m]) for m in model.MARKETS)
        soc = pyo.value(model.soc[t])
        expected = previous_soc + charge * pyo.value(model.eta_c) * pyo.value(model.dt)
        expected -= discharge / pyo.value(model.eta_d) * pyo.value(model.dt)
        max_energy_residual = max(max_energy_residual, abs(soc - expected))
        max_power_violation = max(max_power_violation, charge - pyo.value(model.P_limit),
                                  discharge - pyo.value(model.P_limit), 0.0)
        previous_soc = soc
    terminal_residual = abs(
        pyo.value(model.soc[model.T.last()]) - pyo.value(model.soc_final) * capacity
    )
    residuals = {
        "max_energy_balance_residual_mwh": max_energy_residual,
        "max_power_limit_violation_mw": max_power_violation,
        "terminal_soc_residual_mwh": terminal_residual,
    }
    failed = {name: value for name, value in residuals.items() if value > tolerance}
    if failed:
        raise RuntimeError(f"Solution validation failed at tolerance {tolerance}: {failed}")
    return residuals
