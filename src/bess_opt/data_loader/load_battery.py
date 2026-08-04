"""Loads battery + degradation parameters, routing excel -> database -> yaml default."""
from __future__ import annotations

from typing import Dict

import pandas as pd

from bess_opt.db.connection import get_session
from bess_opt.db.repository import save_battery_params, save_degradation_curve
from bess_opt.excel_io.readers import ExcelReader
from bess_opt.utils.helpers import load_yaml
from bess_opt.utils.logger import get_logger

logger = get_logger(__name__)


def load_battery_params(config: dict, run_name: str) -> Dict[str, float]:
    priority = config["input_source"]["priority"]

    for source in priority:
        if source == "excel":
            try:
                reader = ExcelReader(config["input_source"]["excel_file"])
                params = reader.read_battery_params()
                with get_session(config["database"]["path"]) as session:
                    save_battery_params(session, run_name, params)
                logger.info("Loaded battery params from Excel")
                return params
            except FileNotFoundError:
                continue
        elif source == "database":
            # database params require a prior run_name write; typically
            # falls through to yaml defaults on a first-ever run
            continue

    # Fallback: static YAML defaults, flattened
    yaml_params = load_yaml("config/bess_params.yaml")
    flat = _flatten(yaml_params)
    with get_session(config["database"]["path"]) as session:
        save_battery_params(session, run_name, flat)
    logger.info("Loaded battery params from YAML defaults")
    return flat


def load_degradation_curve(config: dict) -> pd.DataFrame:
    priority = config["input_source"]["priority"]

    for source in priority:
        if source == "excel":
            try:
                reader = ExcelReader(config["input_source"]["excel_file"])
                df = reader.read_degradation_curve()
                with get_session(config["database"]["path"]) as session:
                    save_degradation_curve(session, df)
                return df
            except FileNotFoundError:
                continue

    csv_path = load_yaml("config/bess_params.yaml")["degradation"]["cycle_life_curve_file"]
    from bess_opt.utils.helpers import resolve_path
    df = pd.read_csv(resolve_path(csv_path))
    with get_session(config["database"]["path"]) as session:
        save_degradation_curve(session, df)
    return df


def _flatten(nested: dict, prefix: str = "") -> Dict[str, float]:
    flat = {}
    for k, v in nested.items():
        key = f"{prefix}{k}"
        if isinstance(v, dict):
            flat.update(_flatten(v, prefix=f"{key}."))
        elif isinstance(v, (int, float)):
            flat[key] = float(v)
    return flat
