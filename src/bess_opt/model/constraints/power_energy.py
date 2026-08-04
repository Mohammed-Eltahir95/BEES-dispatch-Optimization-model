"""Core battery physics: power limits, SOC dynamics, throughput accounting."""
from __future__ import annotations

import pyomo.environ as pyo


def add_power_energy_constraints(model: pyo.ConcreteModel) -> pyo.ConcreteModel:

    def total_charge_rule(m, t):
        return sum(m.charge[t, mk] for mk in m.MARKETS) <= m.P_limit * m.is_charging[t]
    model.total_charge_limit = pyo.Constraint(model.T, rule=total_charge_rule)

    def total_discharge_rule(m, t):
        return sum(m.discharge[t, mk] for mk in m.MARKETS) <= m.P_limit * (1 - m.is_charging[t])
    model.total_discharge_limit = pyo.Constraint(model.T, rule=total_discharge_rule)

    def soc_dynamics_rule(m, t):
        charge_in = sum(m.charge[t, mk] for mk in m.MARKETS) * m.eta_c * m.dt
        discharge_out = sum(m.discharge[t, mk] for mk in m.MARKETS) / m.eta_d * m.dt
        if t == m.T.first():
            prev_soc = m.soc_initial * m.E_capacity
        else:
            prev_soc = m.soc[t - 1]
        return m.soc[t] == prev_soc + charge_in - discharge_out
    model.soc_dynamics = pyo.Constraint(model.T, rule=soc_dynamics_rule)

    def soc_bounds_rule(m, t):
        return (m.soc_min * m.E_capacity, m.soc[t], m.soc_max * m.E_capacity)
    model.soc_bounds = pyo.Constraint(model.T, rule=soc_bounds_rule)

    def terminal_soc_rule(m):
        last_t = m.T.last()
        return m.soc[last_t] == m.soc_final * m.E_capacity
    model.terminal_soc = pyo.Constraint(rule=terminal_soc_rule)

    def throughput_rule(m, t):
        charge_total = sum(m.charge[t, mk] for mk in m.MARKETS)
        discharge_total = sum(m.discharge[t, mk] for mk in m.MARKETS)
        return m.throughput[t] == (charge_total + discharge_total) * m.dt
    model.throughput_def = pyo.Constraint(model.T, rule=throughput_rule)

    return model
