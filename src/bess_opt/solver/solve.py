"""Solve wrapper around HiGHS, with fallback between appsi_highs and highs interfaces."""
from __future__ import annotations

import pyomo.environ as pyo

from bess_opt.utils.logger import get_logger

logger = get_logger(__name__)


def solve_model(model: pyo.ConcreteModel, solver_config: dict) -> dict:
    solver_name = solver_config.get("name", "appsi_highs")
    options = solver_config.get("options", {})

    try:
        solver = pyo.SolverFactory(solver_name)
        for key, value in options.items():
            solver.options[key] = value
        logger.info("Solving with %s, options=%s", solver_name, options)
        results = solver.solve(model, tee=options.get("output_flag", False))
    except Exception as e:
        fallback = solver_config.get("fallback", {}).get("name", "highs")
        logger.warning("Primary solver '%s' failed (%s). Falling back to '%s'.",
                        solver_name, e, fallback)
        solver = pyo.SolverFactory(fallback)
        results = solver.solve(model, tee=False)
        solver_name = fallback

    status = str(results.solver.termination_condition)
    logger.info("Solve finished. Termination condition: %s", status)

    return {
        "status": status,
        "solver_name": solver_name,
        "objective_value": pyo.value(model.objective) if _is_optimal(status) else None,
        "raw_results": results,
    }


def _is_optimal(status: str) -> bool:
    return status in ("optimal", "locallyOptimal", "globallyOptimal")
