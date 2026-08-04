from datetime import datetime, timedelta
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bess_opt.validation import validate_inputs


def _valid_inputs():
    times = [datetime(2026, 1, 1) + timedelta(hours=i) for i in range(3)]
    prices = {"day_ahead": pd.Series([20.0, 30.0, 40.0], index=times)}
    params = {
        "battery.energy_capacity_mwh": 10.0,
        "battery.power_limit_mw": 5.0,
        "battery.charge_efficiency": 0.95,
        "battery.discharge_efficiency": 0.95,
        "battery.soc_min_pct": 0.1,
        "battery.soc_max_pct": 0.9,
        "battery.soc_initial_pct": 0.5,
        "battery.soc_final_pct": 0.5,
    }
    return times, prices, params


def test_valid_inputs_pass():
    validate_inputs(*_valid_inputs())


def test_missing_price_is_rejected():
    times, prices, params = _valid_inputs()
    prices["day_ahead"].iloc[1] = float("nan")
    with pytest.raises(ValueError, match="missing or non-finite"):
        validate_inputs(times, prices, params)


def test_invalid_efficiency_is_rejected():
    times, prices, params = _valid_inputs()
    params["battery.charge_efficiency"] = 1.2
    with pytest.raises(ValueError, match="finite fraction"):
        validate_inputs(times, prices, params)


def test_irregular_timestamps_are_rejected():
    times, prices, params = _valid_inputs()
    times[-1] += timedelta(minutes=15)
    with pytest.raises(ValueError, match="constant interval"):
        validate_inputs(times, prices, params)
