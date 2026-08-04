# Methodology

The workflow loads battery parameters and market-price series from an Excel,
SQLite, or REST source; aligns or forecasts missing horizon prices; constructs a
Pyomo mixed-integer linear model; solves it with HiGHS; validates the solution;
and writes dispatch, state-of-charge (SOC), revenue, KPI, and figure outputs.

The objective maximises gross market revenue less a linear throughput-based
degradation proxy and a fixed calendar-aging proxy. A binary charging-state
variable prohibits simultaneous aggregate charging and discharging. Reserve
participation uses a simplified upward-energy headroom constraint. These market
rules are illustrative and require adaptation and validation before operational
use.

The bundled future prices are forecasts from only 24 preceding hourly fixture
values. This is sufficient for software demonstration but not for credible
market forecasting or economic inference.
