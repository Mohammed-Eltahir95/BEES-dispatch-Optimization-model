"""CRUD operations used by data_loader and postprocessing layers."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from bess_opt.db.models import (
    Market, MarketPrice, BatteryParam, DegradationCurve,
    OptimizationRun, DispatchResult,
)


def upsert_market(session: Session, name: str, market_type: str) -> Market:
    existing = session.scalar(select(Market).where(Market.market_name == name))
    if existing:
        return existing
    m = Market(market_name=name, market_type=market_type)
    session.add(m)
    session.flush()
    return m


def save_market_prices(session: Session, market_name: str, market_type: str,
                        prices: pd.Series, source: str = "api") -> None:
    """`prices` is a pandas Series indexed by timestamp (datetime-like)."""
    market = upsert_market(session, market_name, market_type)
    for ts, price in prices.items():
        ts_str = pd.Timestamp(ts).isoformat()
        exists = session.scalar(
            select(MarketPrice).where(
                MarketPrice.market_id == market.market_id,
                MarketPrice.timestamp == ts_str,
                MarketPrice.source == source,
            )
        )
        if exists:
            exists.price = float(price)
        else:
            session.add(MarketPrice(
                market_id=market.market_id, timestamp=ts_str,
                price=float(price), source=source,
            ))


def load_market_prices(session: Session, market_name: str) -> pd.DataFrame:
    rows = session.execute(
        select(MarketPrice.timestamp, MarketPrice.price)
        .join(Market, Market.market_id == MarketPrice.market_id)
        .where(Market.market_name == market_name)
        .order_by(MarketPrice.timestamp)
    ).all()
    return pd.DataFrame(rows, columns=["timestamp", "price"])


def save_battery_params(session: Session, run_name: str, params: dict) -> None:
    for key, value in params.items():
        existing = session.scalar(
            select(BatteryParam).where(
                BatteryParam.run_name == run_name, BatteryParam.parameter == key
            )
        )
        if existing:
            existing.value = float(value)
        else:
            session.add(BatteryParam(run_name=run_name, parameter=key, value=float(value)))


def save_degradation_curve(session: Session, curve_df: pd.DataFrame) -> None:
    session.query(DegradationCurve).delete()
    for _, row in curve_df.iterrows():
        session.add(DegradationCurve(
            dod_pct=float(row["dod_pct"]), cycles_to_eol=float(row["cycles_to_eol"])
        ))


def create_run(session: Session, run_name: str, solver_name: str) -> OptimizationRun:
    run = OptimizationRun(
        run_name=run_name, started_at=datetime.now(timezone.utc).isoformat(),
        status="running", solver_name=solver_name,
    )
    session.add(run)
    session.flush()
    return run


def finish_run(session: Session, run: OptimizationRun, status: str,
                objective_value: float | None) -> None:
    run.finished_at = datetime.now(timezone.utc).isoformat()
    run.status = status
    run.objective_value = objective_value


def save_dispatch_results(session: Session, run_id: int,
                           results: Iterable[dict]) -> None:
    for r in results:
        session.add(DispatchResult(run_id=run_id, **r))
