import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bess_opt.excel_io.readers import ExcelReader

EXCEL_PATH = "data/excel_inputs/inputs_template.xlsx"


def test_read_battery_params():
    reader = ExcelReader(EXCEL_PATH)
    params = reader.read_battery_params()
    assert "battery.energy_capacity_mwh" in params
    assert params["battery.energy_capacity_mwh"] > 0


def test_read_market_prices():
    reader = ExcelReader(EXCEL_PATH)
    df = reader.read_market_prices()
    assert "day_ahead" in df.columns
    assert len(df) == 24


def test_read_degradation_curve():
    reader = ExcelReader(EXCEL_PATH)
    df = reader.read_degradation_curve()
    assert list(df.columns) == ["dod_pct", "cycles_to_eol"]
    assert len(df) > 0
