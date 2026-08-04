"""Defines Pyomo Sets and Params from loaded time series / battery config."""
from __future__ import annotations

from typing import Dict

import pandas as pd
import pyomo.environ as pyo


def add_sets_and_params(model: pyo.ConcreteModel, time_index: list,
                         market_prices: Dict[str, pd.Series],
                         battery_params: Dict[str, float]) -> pyo.ConcreteModel:
    n_steps = len(time_index)
    dt_hours = (time_index[1] - time_index[0]).total_seconds() / 3600.0 if n_steps > 1 else 1.0

    model.T = pyo.RangeSet(0, n_steps - 1)
    model.MARKETS = pyo.Set(initialize=list(market_prices.keys()))
    model.dt = pyo.Param(initialize=dt_hours)

    # Price param: price[t, market]
    price_dict = {
        (t, m): float(series.iloc[t]) if t < len(series) else 0.0
        for m, series in market_prices.items()
        for t in range(n_steps)
    }
    model.price = pyo.Param(model.T, model.MARKETS, initialize=price_dict, default=0.0)

    # Battery params
    model.E_capacity = pyo.Param(initialize=battery_params.get("battery.energy_capacity_mwh", 10.0))
    model.P_limit = pyo.Param(initialize=battery_params.get("battery.power_limit_mw", 5.0))
    model.eta_c = pyo.Param(initialize=battery_params.get("battery.charge_efficiency", 0.95))
    model.eta_d = pyo.Param(initialize=battery_params.get("battery.discharge_efficiency", 0.95))
    model.soc_min = pyo.Param(initialize=battery_params.get("battery.soc_min_pct", 0.1))
    model.soc_max = pyo.Param(initialize=battery_params.get("battery.soc_max_pct", 0.95))
    model.soc_initial = pyo.Param(initialize=battery_params.get("battery.soc_initial_pct", 0.5))
    model.soc_final = pyo.Param(initialize=battery_params.get("battery.soc_final_pct", 0.5))

    # Degradation params
    model.deg_cost_per_mwh = pyo.Param(
        initialize=battery_params.get("degradation.cost_per_mwh_throughput", 4.5)
    )
    model.calendar_fade_per_day = pyo.Param(
        initialize=battery_params.get("degradation.calendar_fade_per_day_pct", 0.005)
    )
    model.max_daily_throughput = pyo.Param(
        initialize=battery_params.get("degradation_constraints.max_daily_throughput_mwh", 20.0)
    )

    return model
