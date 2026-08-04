"""Degradation modeling, kept LP-friendly for HiGHS.

Approach: linearized throughput-based cycle aging cost (cost per MWh cycled,
optionally derived from a piecewise-linear cycle-life curve) plus a fixed
calendar aging term. This avoids nonlinear DoD^exponent formulations that
would require a MINLP solver.
"""
from __future__ import annotations

import pyomo.environ as pyo


def add_degradation_constraints(model: pyo.ConcreteModel) -> pyo.ConcreteModel:

    def daily_throughput_rule(m):
        total = sum(m.throughput[t] for t in m.T)
        return total <= m.max_daily_throughput
    model.daily_throughput_limit = pyo.Constraint(rule=daily_throughput_rule)

    return model


def degradation_cost_expr(model: pyo.ConcreteModel):
    """Returns a Pyomo expression for total degradation cost over the horizon."""
    cycle_cost = sum(model.throughput[t] * model.deg_cost_per_mwh for t in model.T)
    n_days = (len(model.T) * pyo.value(model.dt)) / 24.0
    calendar_cost = model.calendar_fade_per_day * n_days * model.E_capacity * model.deg_cost_per_mwh
    return cycle_cost + calendar_cost
