"""Read battery params, market prices, and degradation curve from an Excel workbook."""
from __future__ import annotations

from typing import Dict

import pandas as pd

from bess_opt.utils.helpers import load_yaml, resolve_path
from bess_opt.utils.logger import get_logger

logger = get_logger(__name__)


class ExcelReader:
    def __init__(self, excel_path: str, config_path: str = "config/excel_config.yaml"):
        self.excel_path = resolve_path(excel_path)
        self.config = load_yaml(config_path)
        if not self.excel_path.exists():
            raise FileNotFoundError(f"Excel input file not found: {self.excel_path}")

    def read_battery_params(self) -> Dict[str, float]:
        sheet = self.config["sheets"]["battery_params"]
        cols = self.config["battery_params_columns"]
        df = pd.read_excel(self.excel_path, sheet_name=sheet)
        params = dict(zip(df[cols["param"]], df[cols["value"]]))
        logger.info("Loaded %d battery params from Excel", len(params))
        return params

    def read_market_prices(self) -> pd.DataFrame:
        sheet = self.config["sheets"]["market_prices"]
        ts_col = self.config["market_prices_columns"]["timestamp"]
        df = pd.read_excel(self.excel_path, sheet_name=sheet)
        df[ts_col] = pd.to_datetime(df[ts_col])
        df = df.set_index(ts_col).sort_index()
        logger.info("Loaded market price sheet with columns: %s", list(df.columns))
        return df  # columns = market names, index = timestamp

    def read_degradation_curve(self) -> pd.DataFrame:
        sheet = self.config["sheets"]["degradation_curve"]
        cols = self.config["degradation_curve_columns"]
        df = pd.read_excel(self.excel_path, sheet_name=sheet)
        df = df.rename(columns={
            cols["depth_of_discharge"]: "dod_pct",
            cols["cycles_to_eol"]: "cycles_to_eol",
        })
        return df[["dod_pct", "cycles_to_eol"]]

    def read_scenario_config(self) -> Dict[str, str]:
        sheet = self.config["sheets"]["scenario_config"]
        df = pd.read_excel(self.excel_path, sheet_name=sheet)
        return dict(zip(df.iloc[:, 0], df.iloc[:, 1]))
