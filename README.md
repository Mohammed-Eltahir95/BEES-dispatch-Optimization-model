# BESS Dispatch Optimisation Model 

A reproducible Python/Pyomo workflow for degradation-aware battery dispatch across energy and reserve price streams using the HiGHS solver.

This repository is a curated and reproducible public release of the project. Exploratory development was conducted separately.

> The included case is a **5 MW / 10 MWh, 24-hour software demonstration**. Its price series is an input fixture without documented market provenance and must not be interpreted as evidence of operational or financial performance.

```mermaid
flowchart LR
  A[Excel, SQLite, or API inputs] --> B[Alignment and validation]
  B --> C[Optional price forecasting]
  C --> D[Pyomo MILP]
  D --> E[HiGHS optimisation]
  E --> F[Independent physical checks]
  F --> G[CSV, Excel, SQLite, and figures]
```

## Overview

The model schedules battery charging and discharging to maximise price-based value net of a linear throughput-degradation proxy. It enforces:

- state-of-charge dynamics and operating bounds;
- aggregate charging and discharging power limits;
- mutually exclusive charging and discharging modes;
- a terminal state-of-charge target;
- a horizon-throughput limit; and
- simplified reserve-energy headroom.

The software separates input handling, forecasting, model formulation, solving, validation, persistence, and visualisation. Detailed methodology and equations are provided in [`docs/`](docs/).

## Demonstration case

| Parameter | Value | Unit |
|---|---:|---|
| Energy capacity | 10 | MWh |
| Power limit | 5 | MW |
| Charge/discharge efficiency | 0.95 / 0.95 | fraction |
| Minimum/maximum SOC | 0.10 / 0.95 | fraction |
| Initial/final SOC | 0.50 / 0.50 | fraction |
| Maximum horizon throughput | 20 | MWh |
| Throughput penalty | 4.5 | unspecified currency/MWh |

The bundled workbook contains 24 hourly day-ahead and FCR fixture values dated 5 July 2026. The default run forecasts the following 24-hour horizon. Forecasted values are explicitly identified in `price_forecast.csv`.

## Installation

Python 3.11 is recommended.

### Conda

```bash
conda env create -f environment.yml
conda activate bess-dispatch-model-gr
python -m pip install -e .
```

### Virtual environment

```bash
python -m venv .venv

# Linux/macOS
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1

python -m pip install -r requirements.txt
python -m pip install -e .
```

## Reproduce the demonstration

From the repository root, run:

```bash
python -m bess_opt.main --config config/config.yaml
```

The command initialises SQLite storage, loads and validates the fixture, prepares the configured price horizon, solves the model, checks the solution, and writes CSV, Excel, SQLite, log, and PNG artifacts under `results/` and `database/`. Generated artifacts are ignored by Git.

## Verification

Run:

```bash
python -m pytest -q
```

The public release contains 27 tests covering input parsing, timestamp alignment, forecasting, database operations, model construction, HiGHS solution, SOC and power constraints, terminal state, KPI calculations, and independent energy-balance validation.

During release verification, all 27 tests passed. The demonstration solved to optimality with:

| Check | Verified value |
|---|---:|
| Maximum energy-balance residual | 1.78 × 10⁻¹⁵ MWh |
| Maximum power-limit violation | 0 MW |
| Terminal-SOC residual | 0 MWh |

These values verify numerical consistency of the fixture; they are not external validation against an operating battery or electricity market.

## Repository structure

```text
config/          run, battery, solver, I/O, and KPI evidence contracts
data/            demonstration workbook, degradation curve, and data policy
database/        SQLite schema and migrations
docs/            methodology, mathematical formulation, validation, limitations
scripts/         data-loading, database, optimisation, and KPI utilities
src/bess_opt/    application package
tests/           automated unit and integration tests
results/         generated-output policy; run artifacts are ignored
```

## Data and evidence policy

The included prices and degradation curve are demonstration inputs without authoritative source citations. They are suitable for testing software behaviour, not for drawing market, revenue, degradation, or investment conclusions.

Any empirical study should record the provider, dataset identifier, retrieval date, licence, timezone, currency, units, preprocessing operations, and checksums. See [`data/README.md`](data/README.md) and [`results/README.md`](results/README.md).

`config/kpi_contract.yaml` and `scripts/evaluate_cv_kpis.py` provide an evidence-driven comparison framework. Target values never enter the optimiser, and missing evidence causes KPI evaluation to fail.

## Limitations

- Reserve participation uses simplified energy headroom rather than complete product-specific activation and settlement rules.
- The objective uses a constant throughput penalty; the included cycle-life curve is not integrated into the formulation.
- Forecasting from the one-day fixture does not establish predictive performance.
- No measured dispatch, externally validated revenue, uncertainty study, or controlled runtime comparison is included.
- Currency and market provenance are unspecified for the demonstration fixture.

See [`docs/limitations.md`](docs/limitations.md) for the full scientific scope.

## Citation and licence

Citation metadata is provided in [`CITATION.cff`](CITATION.cff).

Copyright © 2026 Mohammed Eltahir. This repository is available for academic inspection under [`LICENSE`](LICENSE). Reuse requires prior written permission. Third-party software and data remain subject to their respective terms.
