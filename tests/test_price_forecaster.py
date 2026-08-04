from datetime import datetime, timedelta
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bess_opt.forecasting.price_forecaster import prepare_price_series


def _hourly_index(start: datetime, hours: int) -> pd.DatetimeIndex:
    return pd.DatetimeIndex([start + timedelta(hours=i) for i in range(hours)])


def test_existing_horizon_prices_are_preserved():
    index = _hourly_index(datetime(2026, 1, 1), 24)
    history = pd.Series(np.arange(24, dtype=float), index=index, name="day_ahead")

    prepared = prepare_price_series(history, index, {"enabled": True}, "day_ahead")

    pd.testing.assert_series_equal(prepared, history, check_freq=False)
    assert prepared.attrs["forecasted_timestamps"] == []


def test_future_horizon_is_forecast_from_history():
    history_index = _hourly_index(datetime(2026, 1, 1), 24 * 7)
    hour = np.arange(len(history_index))
    values = 50.0 + 15.0 * np.sin(2.0 * np.pi * hour / 24.0) + 0.02 * hour
    history = pd.Series(values, index=history_index, name="day_ahead")
    target = _hourly_index(datetime(2026, 1, 8), 24)

    prepared = prepare_price_series(
        history,
        target,
        {
            "enabled": True,
            "method": "ridge_regression",
            "minimum_history_points": 12,
            "ridge_alpha": 1.0,
        },
        "day_ahead",
    )

    assert prepared.index.equals(target)
    assert len(prepared) == 24
    assert prepared.notna().all()
    assert np.isfinite(prepared.to_numpy()).all()
    assert len(prepared.attrs["forecasted_timestamps"]) == 24
    assert prepared.max() > prepared.min()


def test_partial_horizon_keeps_observed_and_forecasts_missing():
    history_index = _hourly_index(datetime(2026, 1, 1), 30)
    history = pd.Series(np.linspace(20.0, 40.0, 30), index=history_index, name="fcr")
    target = _hourly_index(datetime(2026, 1, 2), 12)

    prepared = prepare_price_series(history, target, {"enabled": True}, "fcr")

    overlap = target[target <= history.index.max()]
    pd.testing.assert_series_equal(
        prepared.loc[overlap], history.loc[overlap], check_names=False, check_freq=False
    )
    assert prepared.notna().all()
    assert len(prepared.attrs["forecasted_timestamps"]) == len(target) - len(overlap)


def test_missing_future_prices_raise_when_forecasting_disabled():
    history_index = _hourly_index(datetime(2026, 1, 1), 24)
    history = pd.Series(np.arange(24, dtype=float), index=history_index)
    target = _hourly_index(datetime(2026, 1, 2), 24)

    with pytest.raises(ValueError, match="Forecasting is disabled"):
        prepare_price_series(history, target, {"enabled": False}, "day_ahead")


def test_short_history_uses_fallback_without_nan():
    history_index = _hourly_index(datetime(2026, 1, 1), 4)
    history = pd.Series([10.0, 20.0, 30.0, 40.0], index=history_index)
    target = _hourly_index(datetime(2026, 1, 1, 4), 6)

    prepared = prepare_price_series(
        history,
        target,
        {"enabled": True, "minimum_history_points": 12},
        "afrr",
    )

    assert prepared.notna().all()
    assert np.isfinite(prepared.to_numpy()).all()


def test_excel_loader_forecasts_configured_future_horizon(tmp_path):
    from bess_opt.data_loader.load_prices import load_all_market_prices
    from bess_opt.db.connection import init_db_from_schema, reset_engine_cache

    project_root = Path(__file__).resolve().parents[1]
    db_path = tmp_path / "forecast_test.db"
    reset_engine_cache(str(db_path))
    init_db_from_schema(str(db_path))

    config = {
        "input_source": {
            "priority": ["excel"],
            "excel_file": str(project_root / "data/excel_inputs/inputs_template.xlsx"),
        },
        "markets": [
            {"name": "day_ahead", "enabled": True, "type": "energy"},
            {"name": "fcr", "enabled": True, "type": "reserve"},
        ],
        "database": {"path": str(db_path), "cache_api_results": True},
        "forecasting": {
            "enabled": True,
            "method": "ridge_regression",
            "minimum_history_points": 12,
            "ridge_alpha": 10.0,
        },
    }
    target = _hourly_index(datetime(2026, 7, 6), 24)

    prices = load_all_market_prices(config, time_index=target)

    assert set(prices) == {"day_ahead", "fcr"}
    for series in prices.values():
        assert series.index.equals(target)
        assert series.notna().all()
        assert len(series.attrs["forecasted_timestamps"]) == 24
