# Validation

Automated checks cover monotonic, unique, equally spaced timestamps; finite
prices; positive capacities; efficiencies and SOC fractions in `(0, 1]`; SOC
ordering; power and SOC limits; terminal SOC; throughput; and an independently
recalculated stepwise energy balance. Unit tests also solve a small deterministic
model with HiGHS when the dependency is available.

No comparison with an independent dispatch tool, historical operator schedule,
or measured battery data is committed. Consequently, a claimed validation
deviation below 1.5% is not currently reproducible.
