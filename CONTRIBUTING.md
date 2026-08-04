# Contributing

Contributions should preserve the documented mathematical formulation and must
not replace reference outputs without explaining the scientific reason.

1. Create a focused branch and describe the research question addressed.
2. Add or update tests for energy balance, power/SOC bounds, units, timestamps,
   and any changed market rule.
3. Run `python -m pytest -q` and the reproduction command in `README.md`.
4. Record user-visible changes in `CHANGELOG.md`.
5. Do not commit credentials, raw licensed market data, databases, logs, or
   generated figures. Document provenance and redistribution rights for new data.

Bug reports should include the configuration, Python/package versions, solver
termination condition, and a minimal redistributable input.
