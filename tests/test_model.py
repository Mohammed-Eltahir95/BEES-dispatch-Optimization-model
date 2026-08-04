import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd
import pyomo.environ as pyo

from bess_opt.model.build_model import build_model


def _sample_inputs():
    start = datetime(2026, 7, 5, 0, 0, 0)
    time_index = [start + timedelta(hours=i) for i in range(4)]
    prices = {
        "day_ahead": pd.Series([30, 40, 20, 50], index=time_index),
        "fcr": pd.Series([10, 10, 10, 10], index=time_index),
    }
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
    market_config = [
        {"name": "day_ahead", "enabled": True, "type": "energy"},
        {"name": "fcr", "enabled": True, "type": "reserve"},
    ]
    return time_index, prices, battery_params, market_config


def test_build_model_has_expected_components():
    time_index, prices, battery_params, market_config = _sample_inputs()
    model = build_model(time_index, prices, battery_params, market_config)

    assert hasattr(model, "charge")
    assert hasattr(model, "discharge")
    assert hasattr(model, "soc")
    assert hasattr(model, "objective")
    assert len(model.T) == 4


def test_model_solves_with_highs():
    time_index, prices, battery_params, market_config = _sample_inputs()
    model = build_model(time_index, prices, battery_params, market_config)

    solver = pyo.SolverFactory("appsi_highs")
    results = solver.solve(model)
    assert str(results.solver.termination_condition) in ("optimal", "locallyOptimal")
