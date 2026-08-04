# Mathematical formulation

For time step `t` and market `m`, charging and discharging powers are
`P_charge[t,m]` and `P_discharge[t,m]` (MW), SOC is `E[t]` (MWh), price is
`pi[t,m]` (currency/MWh), and step length is `dt` (h).

The implemented objective is

`max sum_t,m ((P_discharge - P_charge) * pi * dt) - c_deg * sum_t throughput[t] - C_calendar`.

The state equation is

`E[t] = E[t-1] + eta_c * sum_m(P_charge[t,m]) * dt - sum_m(P_discharge[t,m]) * dt / eta_d`.

Aggregate charge and discharge are each limited by rated power and made mutually
exclusive by a binary state. SOC remains between configured fractions of energy
capacity, final SOC equals its configured target, and horizon throughput is
bounded. The calendar term is constant for a fixed horizon and therefore does
not alter dispatch decisions.

## Parameters

| Parameter | Fixture value | Unit | Role |
|---|---:|---|---|
| Energy capacity | 10 | MWh | SOC scaling |
| Power limit | 5 | MW | Aggregate charge/discharge limit |
| Charge/discharge efficiency | 0.95 / 0.95 | fraction | Energy balance |
| SOC min/max/initial/final | 0.10 / 0.95 / 0.50 / 0.50 | fraction | Operating bounds |
| Degradation proxy | 4.5 | currency/MWh throughput | Objective penalty |
| Maximum horizon throughput | 20 | MWh | Cycling constraint |

Currency is not consistently specified by the fixture and is `[TO BE COMPLETED]`.
