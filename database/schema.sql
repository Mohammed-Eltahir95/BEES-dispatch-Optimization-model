-- BESS Multi-Market Optimization: SQLite schema

CREATE TABLE IF NOT EXISTS markets (
    market_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    market_name   TEXT UNIQUE NOT NULL,
    market_type   TEXT NOT NULL          -- 'energy' | 'reserve'
);

CREATE TABLE IF NOT EXISTS market_prices (
    price_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    market_id     INTEGER NOT NULL REFERENCES markets(market_id),
    timestamp     TEXT NOT NULL,          -- ISO 8601
    price         REAL NOT NULL,
    source        TEXT DEFAULT 'api',     -- 'api' | 'excel' | 'manual'
    UNIQUE(market_id, timestamp, source)
);

CREATE TABLE IF NOT EXISTS battery_params (
    param_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    run_name      TEXT NOT NULL,
    parameter     TEXT NOT NULL,
    value         REAL NOT NULL,
    UNIQUE(run_name, parameter)
);

CREATE TABLE IF NOT EXISTS degradation_curve (
    curve_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    dod_pct       REAL NOT NULL,
    cycles_to_eol REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS optimization_runs (
    run_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    run_name      TEXT NOT NULL,
    started_at    TEXT NOT NULL,
    finished_at   TEXT,
    status        TEXT,                  -- 'success' | 'failed' | 'infeasible'
    objective_value REAL,
    solver_name   TEXT,
    notes         TEXT
);

CREATE TABLE IF NOT EXISTS dispatch_results (
    result_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id        INTEGER NOT NULL REFERENCES optimization_runs(run_id),
    timestamp     TEXT NOT NULL,
    market_id     INTEGER REFERENCES markets(market_id),
    charge_mw     REAL,
    discharge_mw  REAL,
    soc_mwh       REAL,
    revenue       REAL,
    degradation_cost REAL
);

CREATE INDEX IF NOT EXISTS idx_prices_market_ts ON market_prices(market_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_dispatch_run ON dispatch_results(run_id);
