"""Pulls solved variable values out of the Pyomo model into tidy DataFrames."""
from __future__ import annotations

import pandas as pd
import pyomo.environ as pyo


def extract_dispatch(model: pyo.ConcreteModel, time_index: list) -> pd.DataFrame:
    rows = []
    for t in model.T:
        for mk in model.MARKETS:
            rows.append({
                "timestamp": time_index[t],
                "market": mk,
                "charge_mw": pyo.value(model.charge[t, mk]),
                "discharge_mw": pyo.value(model.discharge[t, mk]),
                "price": pyo.value(model.price[t, mk]),
                "revenue": (pyo.value(model.discharge[t, mk]) - pyo.value(model.charge[t, mk]))
                           * pyo.value(model.price[t, mk]) * pyo.value(model.dt),
            })
    return pd.DataFrame(rows)


def extract_soc(model: pyo.ConcreteModel, time_index: list) -> pd.DataFrame:
    rows = [{"timestamp": time_index[t], "soc_mwh": pyo.value(model.soc[t])} for t in model.T]
    return pd.DataFrame(rows)


def extract_revenue_summary(dispatch_df: pd.DataFrame) -> pd.DataFrame:
    return dispatch_df.groupby("market", as_index=False)["revenue"].sum()


def extract_kpis(model: pyo.ConcreteModel, dispatch_df: pd.DataFrame,
                  soc_df: pd.DataFrame, objective_value: float | None) -> pd.DataFrame:
    total_throughput = sum(pyo.value(model.throughput[t]) for t in model.T)
    kpis = {
        "objective_value": objective_value,
        "total_revenue": dispatch_df["revenue"].sum(),
        "total_throughput_mwh": total_throughput,
        "avg_soc_mwh": soc_df["soc_mwh"].mean(),
        "min_soc_mwh": soc_df["soc_mwh"].min(),
        "max_soc_mwh": soc_df["soc_mwh"].max(),
    }
    return pd.DataFrame([kpis])
