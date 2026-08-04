"""Objective: maximize (multi-market revenue - degradation cost)."""
from __future__ import annotations

import pyomo.environ as pyo

from bess_opt.model.constraints.degradation import degradation_cost_expr


def add_objective(model: pyo.ConcreteModel) -> pyo.ConcreteModel:

    def revenue_expr(m):
        return sum(
            (m.discharge[t, mk] - m.charge[t, mk]) * m.price[t, mk] * m.dt
            for t in m.T for mk in m.MARKETS
        )

    def objective_rule(m):
        return revenue_expr(m) - degradation_cost_expr(m)

    model.objective = pyo.Objective(rule=objective_rule, sense=pyo.maximize)
    return model
