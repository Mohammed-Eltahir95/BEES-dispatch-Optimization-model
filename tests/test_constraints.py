import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd
import pyomo.environ as pyo

from bess_opt.model.build_model import build_model


def _sample_model():
    start = datetime(2026, 7, 5, 0, 0, 0)
    time_index = [start + timedelta(hours=i) for i in range(4)]
    prices = {"day_ahead": pd.Series([30, 40, 20, 50], index=time_index)}
    battery_params = {
        "battery.energy_capacity_mwh": 10.0,
        "battery.power_limit_mw": 5.0,
        "battery.charge_efficiency": 0.95,
        "battery.discharge_efficiency": 0.95,
        "battery.soc_min_pct": 0.1,
        "battery.soc_max_pct": 0.95,
        "battery.soc_initial_pct": 0.5,
        "battery.soc_final_pct": 0.5,
        "degradation.cost_per_mwh_throughput": 4.5,
        "degradation.calendar_fade_per_day_pct": 0.005,
        "degradation_constraints.max_daily_throughput_mwh": 20.0,
    }
    market_config = [{"name": "day_ahead", "enabled": True, "type": "energy"}]
    return build_model(time_index, prices, battery_params, market_config)


def test_soc_stays_within_bounds_after_solve():
    model = _sample_model()
    pyo.SolverFactory("appsi_highs").solve(model)
    for t in model.T:
        soc_val = pyo.value(model.soc[t])
        assert pyo.value(model.soc_min) * pyo.value(model.E_capacity) - 1e-6 <= soc_val
        assert soc_val <= pyo.value(model.soc_max) * pyo.value(model.E_capacity) + 1e-6


def test_terminal_soc_constraint_enforced():
    model = _sample_model()
    pyo.SolverFactory("appsi_highs").solve(model)
    last_t = model.T.last()
    expected = pyo.value(model.soc_final) * pyo.value(model.E_capacity)
    assert abs(pyo.value(model.soc[last_t]) - expected) < 1e-6
