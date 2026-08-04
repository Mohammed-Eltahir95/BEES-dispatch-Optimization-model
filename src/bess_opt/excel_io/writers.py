"""Export optimization results back into a formatted Excel workbook."""
from __future__ import annotations

import pandas as pd

from bess_opt.utils.helpers import load_yaml, resolve_path, ensure_dir
from bess_opt.utils.logger import get_logger

logger = get_logger(__name__)


class ExcelWriter:
    def __init__(self, config_path: str = "config/excel_config.yaml"):
        self.config = load_yaml(config_path)

    def export_results(self, output_path: str, dispatch_df: pd.DataFrame,
                        soc_df: pd.DataFrame, revenue_df: pd.DataFrame,
                        kpis_df: pd.DataFrame) -> None:
        sheets = self.config["output_export"]["sheets"]
        out_path = resolve_path(output_path)
        ensure_dir(out_path.parent)

        with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
            dispatch_df.to_excel(writer, sheet_name=sheets["dispatch"], index=False)
            soc_df.to_excel(writer, sheet_name=sheets["soc"], index=False)
            revenue_df.to_excel(writer, sheet_name=sheets["revenue"], index=False)
            kpis_df.to_excel(writer, sheet_name=sheets["kpis"], index=False)

        logger.info("Exported results to %s", out_path)
