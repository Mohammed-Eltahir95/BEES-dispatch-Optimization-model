"""Decision variables: per-market charge/discharge allocation, SOC, throughput."""
from __future__ import annotations

import pyomo.environ as pyo


def add_variables(model: pyo.ConcreteModel) -> pyo.ConcreteModel:
    # Power allocated to charging/discharging per market at each timestep (MW)
    model.charge = pyo.Var(model.T, model.MARKETS, domain=pyo.NonNegativeReals)
    model.discharge = pyo.Var(model.T, model.MARKETS, domain=pyo.NonNegativeReals)

    # Binary flag to prevent simultaneous charge+discharge in the same step
    model.is_charging = pyo.Var(model.T, domain=pyo.Binary)

    # State of charge (MWh), tracked at the end of each timestep
    model.soc = pyo.Var(model.T, domain=pyo.NonNegativeReals)

    # Total energy throughput (MWh) used for degradation cost accounting
    model.throughput = pyo.Var(model.T, domain=pyo.NonNegativeReals)

    return model
