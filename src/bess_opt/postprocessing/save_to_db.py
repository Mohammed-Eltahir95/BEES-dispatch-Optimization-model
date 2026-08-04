"""Persists optimization run metadata and dispatch results into SQLite."""
from __future__ import annotations

import pandas as pd
from sqlalchemy import select

from bess_opt.db.connection import get_session
from bess_opt.db.models import Market
from bess_opt.db.repository import create_run, finish_run, save_dispatch_results
from bess_opt.utils.logger import get_logger

logger = get_logger(__name__)


def persist_run(db_path: str, run_name: str, solver_name: str, status: str,
                 objective_value: float | None, dispatch_df: pd.DataFrame) -> int:
    with get_session(db_path) as session:
        run = create_run(session, run_name, solver_name)
        finish_run(session, run, status, objective_value)
        session.flush()

        market_id_map = {
            m.market_name: m.market_id for m in session.scalars(select(Market)).all()
        }

        records = []
        for _, row in dispatch_df.iterrows():
            records.append({
                "timestamp": pd.Timestamp(row["timestamp"]).isoformat(),
                "market_id": market_id_map.get(row["market"]),
                "charge_mw": row["charge_mw"],
                "discharge_mw": row["discharge_mw"],
                "soc_mwh": None,
                "revenue": row["revenue"],
                "degradation_cost": None,
            })
        save_dispatch_results(session, run.run_id, records)
        logger.info("Persisted run %d (%s) with %d dispatch rows", run.run_id, status, len(records))
        return run.run_id
