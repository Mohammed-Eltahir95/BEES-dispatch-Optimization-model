"""Market-specific rules: capacity availability, reserve minimums, etc.
Kept separate so markets can be added/removed without touching battery physics."""
from __future__ import annotations

import pyomo.environ as pyo


def add_market_constraints(model: pyo.ConcreteModel, market_config: list[dict]) -> pyo.ConcreteModel:
    reserve_markets = [m["name"] for m in market_config if m["type"] == "reserve" and m["enabled"]]
    energy_markets = [m["name"] for m in market_config if m["type"] == "energy" and m["enabled"]]

    # Example: reserve market bids must be backed by available headroom in SOC
    # (simplified linear proxy — refine per actual market product rules, e.g. FCR symmetric bands)
    if reserve_markets:
        def reserve_headroom_rule(m, t, mk):
            if mk not in reserve_markets:
                return pyo.Constraint.Skip
            headroom_up = (m.soc[t] - m.soc_min * m.E_capacity) / m.dt
            return m.discharge[t, mk] <= headroom_up
        model.reserve_headroom = pyo.Constraint(model.T, model.MARKETS, rule=reserve_headroom_rule)

    # Example: energy market (day-ahead) has no special constraint beyond power/SOC limits,
    # already enforced in power_energy.py. Placeholder left for gate closure / block bids etc.

    return model
