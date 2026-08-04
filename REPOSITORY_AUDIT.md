# Prioritised repository audit

| Issue | Importance | Recommended action | File affected |
|---|---|---|---|
| Headline CV KPIs have no committed evidence | Critical | Publish traceable configurations, inputs, logs, baseline comparisons, and outputs before making claims | `results/`, README |
| Fixture is 10 MWh / 5 MW, not 100 MW | Critical | Correct CV or add and validate a separate 100 MW configuration | `data/excel_inputs/inputs_template.xlsx`, `config/bess_params.yaml` |
| Only 24 hourly price rows are present | Critical | Document/source licensed 2023–2026 data before claiming that coverage | fixture workbook, `data/README.md` |
| Reserve products are simplified as charge/discharge energy | High | Implement and validate product-specific capacity, activation, duration, and settlement rules | `model/objective.py`, `market_constraints.py` |
| Degradation curve is not used by optimisation | High | Either integrate a validated piecewise model or describe the constant-throughput proxy only | `load_battery.py`, `degradation.py` |
| API base URL setting named a URL as an environment-variable key | High | Use `MARKET_API_BASE_URL` consistently (corrected on research branch) | `config/api_config.yaml`, `.env.example` |
| Tracked generated SQLite test database | Medium | Stop tracking it in a future intentional commit; tests recreate it and ignore rules now cover it | `tests/tmp_test.db` |
| Generated scientific results are ignored and absent | Medium | Attach a versioned release result bundle with provenance rather than silently committing ad hoc runs | `results/` |
| No independent solution checks | High | Validate inputs and independently recompute physical residuals (added) | `validation.py`, `tests/test_validation.py` |
| Dependency ranges lacked a second reproducible environment | Medium | Maintain `environment.yml` and capture an exact environment export per release | dependency files |
| Data provenance/licensing unspecified | High | Record provider, licence, retrieval, units, timezone, transformations, checksums | `data/README.md` |
| Notebook is a placeholder/exploratory artifact | Low | Keep outside the final execution path and label analyses clearly | `notebooks/exploratory_analysis.ipynb` |
