"""Standalone script: pulls market prices from the API and caches into SQLite.
Useful for a scheduled/cron job that pre-fetches next-day prices."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bess_opt.utils.helpers import load_yaml
from bess_opt.api.market_api import MarketAPI
from bess_opt.db.connection import get_session, init_db_from_schema
from bess_opt.db.repository import save_market_prices

if __name__ == "__main__":
    config = load_yaml("config/config.yaml")
    init_db_from_schema(config["database"]["path"])

    api = MarketAPI()
    horizon = config["horizon"]

    for market_cfg in config["markets"]:
        if not market_cfg["enabled"]:
            continue
        name, mtype = market_cfg["name"], market_cfg["type"]
        series = api.fetch_prices(name, start=horizon["start"], end=None)
        with get_session(config["database"]["path"]) as session:
            save_market_prices(session, name, mtype, series, source="api")
        print(f"Cached {len(series)} price points for '{name}'")
