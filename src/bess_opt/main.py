"""Entry point: loads config + data, builds & solves the Pyomo model, saves results."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from bess_opt.utils.helpers import load_yaml, build_time_index, ensure_dir
from bess_opt.utils.logger import get_logger
from bess_opt.db.connection import init_db_from_schema
from bess_opt.data_loader.load_prices import load_all_market_prices
from bess_opt.data_loader.load_battery import load_battery_params
from bess_opt.model.build_model import build_model
from bess_opt.solver.solve import solve_model
from bess_opt.postprocessing.extract_results import (
    extract_dispatch, extract_soc, extract_revenue_summary, extract_kpis,
)
from bess_opt.postprocessing.save_to_db import persist_run
from bess_opt.postprocessing.plots import plot_soc, plot_dispatch, plot_revenue_breakdown
from bess_opt.excel_io.writers import ExcelWriter
from bess_opt.validation import validate_inputs, validate_solution


def main(config_path: str = "config/config.yaml"):
    config = load_yaml(config_path)
    logger = get_logger("bess_opt.main", log_file=config["logging"]["file"],
                         level=config["logging"]["level"])

    logger.info("=== Starting run: %s ===", config["run_name"])

    init_db_from_schema(config["database"]["path"])

    time_index = build_time_index(
        config["horizon"]["start"], config["horizon"]["hours"], config["horizon"]["timestep_minutes"]
    )

    market_prices = load_all_market_prices(config, time_index=time_index)
    battery_params = load_battery_params(config, config["run_name"])
    validate_inputs(time_index, market_prices, battery_params)

    model = build_model(time_index, market_prices, battery_params, config["markets"])
    solve_result = solve_model(model, config["solver"])

    if solve_result["objective_value"] is None:
        raise RuntimeError(
            f"Optimization did not terminate optimally: {solve_result['status']}"
        )
    validation_residuals = validate_solution(model)
    logger.info("Validation residuals: %s", validation_residuals)

    logger.info("Objective value: %s", solve_result["objective_value"])

    dispatch_df = extract_dispatch(model, time_index)
    soc_df = extract_soc(model, time_index)
    revenue_df = extract_revenue_summary(dispatch_df)
    kpis_df = extract_kpis(model, dispatch_df, soc_df, solve_result["objective_value"])

    ensure_dir(config["output"]["results_dir"])

    price_input_df = pd.DataFrame({"timestamp": time_index})
    for market, series in market_prices.items():
        aligned = series.reindex(time_index)
        price_input_df[market] = aligned.to_numpy(dtype=float)
        forecasted = set(pd_ts for pd_ts in series.attrs.get("forecasted_timestamps", []))
        price_input_df[f"{market}_is_forecast"] = [
            ts.isoformat() in forecasted for ts in aligned.index
        ]
    price_input_path = config.get("forecasting", {}).get(
        "output_file", f"{config['output']['results_dir']}/price_forecast.csv"
    )
    ensure_dir(Path(price_input_path).parent)
    price_input_df.to_csv(price_input_path, index=False)
    dispatch_df.to_csv(f"{config['output']['results_dir']}/dispatch_schedule.csv", index=False)
    soc_df.to_csv(f"{config['output']['results_dir']}/soc_profile.csv", index=False)
    revenue_df.to_csv(f"{config['output']['results_dir']}/revenue_breakdown.csv", index=False)
    kpis_df.to_csv(f"{config['output']['results_dir']}/kpis.csv", index=False)

    persist_run(
        config["database"]["path"], config["run_name"], solve_result["solver_name"],
        solve_result["status"], solve_result["objective_value"], dispatch_df,
    )

    plot_soc(soc_df, config["output"]["figures_dir"])
    plot_dispatch(dispatch_df, config["output"]["figures_dir"])
    plot_revenue_breakdown(revenue_df, config["output"]["figures_dir"])

    if config["output"].get("export_excel", False):
        ExcelWriter().export_results(
            config["output"]["export_excel_path"], dispatch_df, soc_df, revenue_df, kpis_df
        )

    logger.info("=== Run complete ===")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run BESS multi-market optimization")
    parser.add_argument("--config", default="config/config.yaml", help="Path to config.yaml")
    args = parser.parse_args()
    main(args.config)
