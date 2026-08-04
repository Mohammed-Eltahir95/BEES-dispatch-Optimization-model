-- Migration 001: initial schema
-- Run via scripts/init_db.py; kept here for version history / manual replay.

.read database/schema.sql

INSERT OR IGNORE INTO markets (market_name, market_type) VALUES
    ('day_ahead', 'energy'),
    ('fcr', 'reserve'),
    ('afrr', 'reserve');
