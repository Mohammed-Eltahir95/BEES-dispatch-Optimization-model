# Changelog

## [1.0.0] - 2026-08-04

### Added

- Academic project documentation, citation metadata, reproducible Conda
  environment, data/result provenance notes, and explicit limitations.
- Input and solution validation for timestamps, units/ranges, SOC, power,
  terminal state, throughput, and stepwise energy balance.
- Tests for invalid parameters and independently calculated energy balance.
- Headless, file-only matplotlib rendering for CI and server reproducibility.
- Evidence-driven KPI contract, reusable metric calculations, CLI evaluator, and
  tests that report unmet targets without changing optimisation outputs.

### Clarified

- The committed workbook is a 10 MWh / 5 MW, 24-hour software fixture; it is
  not evidence for a 100 MW deployment or a 2023–2026 market-data study.
- No percentage improvement, validation-deviation, or runtime benchmark is
  claimed without committed reproducible evidence.
