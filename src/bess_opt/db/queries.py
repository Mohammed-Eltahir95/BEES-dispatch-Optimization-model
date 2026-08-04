"""Reusable raw SQL for reporting/analysis that's awkward via the ORM."""

LATEST_RUN_SUMMARY = """
SELECT run_id, run_name, started_at, finished_at, status, objective_value
FROM optimization_runs
ORDER BY started_at DESC
LIMIT 1;
"""

DISPATCH_FOR_RUN = """
SELECT d.timestamp, m.market_name, d.charge_mw, d.discharge_mw,
       d.soc_mwh, d.revenue, d.degradation_cost
FROM dispatch_results d
LEFT JOIN markets m ON m.market_id = d.market_id
WHERE d.run_id = :run_id
ORDER BY d.timestamp;
"""

REVENUE_BY_MARKET = """
SELECT m.market_name, SUM(d.revenue) AS total_revenue
FROM dispatch_results d
JOIN markets m ON m.market_id = d.market_id
WHERE d.run_id = :run_id
GROUP BY m.market_name;
"""
