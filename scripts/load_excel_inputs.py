"""Standalone script: reads the Excel input workbook and loads
battery params, market prices, and the degradation curve into SQLite."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bess_opt.utils.helpers import load_yaml
from bess_opt.excel_io.readers import ExcelReader
from bess_opt.db.connection import get_session, init_db_from_schema
from bess_opt.db.repository import save_market_prices, save_battery_params, save_degradation_curve

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True, help="Path to the Excel input workbook")
    parser.add_argument("--run-name", default="excel_import", help="Label under which battery params are stored")
    args = parser.parse_args()

    config = load_yaml("config/config.yaml")
    init_db_from_schema(config["database"]["path"])

    reader = ExcelReader(args.file)

    params = reader.read_battery_params()
    prices_df = reader.read_market_prices()
    curve_df = reader.read_degradation_curve()

    with get_session(config["database"]["path"]) as session:
        save_battery_params(session, args.run_name, params)
        save_degradation_curve(session, curve_df)
        for market_cfg in config["markets"]:
            name = market_cfg["name"]
            if name in prices_df.columns:
                save_market_prices(session, name, market_cfg["type"], prices_df[name].dropna(), source="excel")

    print(f"Loaded Excel inputs from {args.file} into database "
          f"({config['database']['path']})")
