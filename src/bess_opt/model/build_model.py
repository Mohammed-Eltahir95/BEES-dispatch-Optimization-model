"""Assembles the full Pyomo ConcreteModel from loaded inputs."""
from __future__ import annotations

from typing import Dict

import pandas as pd
import pyomo.environ as pyo

from bess_opt.model.sets_params import add_sets_and_params
from bess_opt.model.variables import add_variables
from bess_opt.model.constraints.power_energy import add_power_energy_constraints
from bess_opt.model.constraints.market_constraints import add_market_constraints
from bess_opt.model.constraints.degradation import add_degradation_constraints
from bess_opt.model.objective import add_objective


def build_model(time_index: list, market_prices: Dict[str, pd.Series],
                 battery_params: dict, market_config: list[dict]) -> pyo.ConcreteModel:
    model = pyo.ConcreteModel(name="BESS_MultiMarket_Degradation")

    model = add_sets_and_params(model, time_index, market_prices, battery_params)
    model = add_variables(model)
    model = add_power_energy_constraints(model)
    model = add_market_constraints(model, market_config)
    model = add_degradation_constraints(model)
    model = add_objective(model)

    return model
