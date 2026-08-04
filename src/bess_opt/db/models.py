"""SQLAlchemy ORM models mirroring database/schema.sql."""
from __future__ import annotations

from sqlalchemy import Column, Integer, String, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Market(Base):
    __tablename__ = "markets"

    market_id = Column(Integer, primary_key=True, autoincrement=True)
    market_name = Column(String, unique=True, nullable=False)
    market_type = Column(String, nullable=False)

    prices = relationship("MarketPrice", back_populates="market")


class MarketPrice(Base):
    __tablename__ = "market_prices"
    __table_args__ = (UniqueConstraint("market_id", "timestamp", "source"),)

    price_id = Column(Integer, primary_key=True, autoincrement=True)
    market_id = Column(Integer, ForeignKey("markets.market_id"), nullable=False)
    timestamp = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    source = Column(String, default="api")

    market = relationship("Market", back_populates="prices")


class BatteryParam(Base):
    __tablename__ = "battery_params"
    __table_args__ = (UniqueConstraint("run_name", "parameter"),)

    param_id = Column(Integer, primary_key=True, autoincrement=True)
    run_name = Column(String, nullable=False)
    parameter = Column(String, nullable=False)
    value = Column(Float, nullable=False)


class DegradationCurve(Base):
    __tablename__ = "degradation_curve"

    curve_id = Column(Integer, primary_key=True, autoincrement=True)
    dod_pct = Column(Float, nullable=False)
    cycles_to_eol = Column(Float, nullable=False)


class OptimizationRun(Base):
    __tablename__ = "optimization_runs"

    run_id = Column(Integer, primary_key=True, autoincrement=True)
    run_name = Column(String, nullable=False)
    started_at = Column(String, nullable=False)
    finished_at = Column(String)
    status = Column(String)
    objective_value = Column(Float)
    solver_name = Column(String)
    notes = Column(String)


class DispatchResult(Base):
    __tablename__ = "dispatch_results"

    result_id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(Integer, ForeignKey("optimization_runs.run_id"), nullable=False)
    timestamp = Column(String, nullable=False)
    market_id = Column(Integer, ForeignKey("markets.market_id"))
    charge_mw = Column(Float)
    discharge_mw = Column(Float)
    soc_mwh = Column(Float)
    revenue = Column(Float)
    degradation_cost = Column(Float)
