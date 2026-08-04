import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd

from bess_opt.db.connection import init_db_from_schema, get_session, reset_engine_cache
from bess_opt.db.repository import (
    save_market_prices, load_market_prices, save_battery_params, create_run, finish_run,
)

TEST_DB_PATH = "tests/tmp_test.db"


def _fresh_db():
    reset_engine_cache(TEST_DB_PATH)
    full_path = Path(__file__).resolve().parents[1] / TEST_DB_PATH
    if full_path.exists():
        full_path.unlink()
    init_db_from_schema(TEST_DB_PATH)
    return TEST_DB_PATH


def test_save_and_load_market_prices():
    db_path = _fresh_db()
    prices = pd.Series(
        [30.0, 40.0, 25.0],
        index=pd.date_range("2026-07-05", periods=3, freq="h"),
    )
    with get_session(db_path) as session:
        save_market_prices(session, "day_ahead", "energy", prices, source="test")

    with get_session(db_path) as session:
        df = load_market_prices(session, "day_ahead")

    assert len(df) == 3
    assert df["price"].tolist() == [30.0, 40.0, 25.0]


def test_save_battery_params_upsert():
    db_path = _fresh_db()
    with get_session(db_path) as session:
        save_battery_params(session, "test_run", {"battery.power_limit_mw": 5.0})
        save_battery_params(session, "test_run", {"battery.power_limit_mw": 7.5})

    with get_session(db_path) as session:
        from bess_opt.db.models import BatteryParam
        from sqlalchemy import select
        row = session.scalar(
            select(BatteryParam).where(
                BatteryParam.run_name == "test_run",
                BatteryParam.parameter == "battery.power_limit_mw",
            )
        )
        assert row.value == 7.5


def test_create_and_finish_run():
    db_path = _fresh_db()
    with get_session(db_path) as session:
        run = create_run(session, "test_run", "appsi_highs")
        finish_run(session, run, "optimal", 1234.5)
        session.flush()
        assert run.status == "optimal"
        assert run.objective_value == 1234.5
