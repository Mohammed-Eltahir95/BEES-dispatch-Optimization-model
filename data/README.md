# Data availability and provenance

`excel_inputs/inputs_template.xlsx` is a small software fixture containing a
10 MWh / 5 MW battery configuration and 24 hourly values for 5 July 2026. The
repository does not establish those price values as observations from a named
market provider; they must therefore be treated as demonstration inputs, not as
research data. `degradation/cycle_life_curve.csv` is likewise an illustrative
curve with no cited experimental provenance.

Place distributable source data in `raw/` and derived data in `processed/`.
Record provider, retrieval date, licence, timezone, units, checksums, and every
preprocessing step. Do not commit confidential or provider-restricted data.
