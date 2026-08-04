"""Loads market price series, routing through excel -> database -> api
per the priority list in config.yaml. Whatever is fetched from the API
gets cached (write-through) into SQLite for reproducibility."""
from __future__ import annotations

from typing import Dict, Iterable

import pandas as pd

from bess_opt.db.connection import get_session
from bess_opt.db.repository import save_market_prices, load_market_prices
from bess_opt.excel_io.readers import ExcelReader
from bess_opt.forecasting.price_forecaster import prepare_price_series
from bess_opt.utils.logger import get_logger

logger = get_logger(__name__)


def load_all_market_prices(
    config: dict, time_index: Iterable[pd.Timestamp] | None = None
) -> Dict[str, pd.Series]:
    """Return prices for enabled markets, forecasting missing horizon values.

    When ``time_index`` is supplied, each raw source series is aligned to the
    optimization horizon. Existing values are preserved and missing future
    timestamps are generated from the configured forecasting model.
    """
    priority = config["input_source"]["priority"]
    markets = [m["name"] for m in config["markets"] if m["enabled"]]
    db_path = config["database"]["path"]

    result: Dict[str, pd.Series] = {}

    for market in markets:
        series = None
        for source in priority:
            if source == "excel":
                series = _try_excel(config, market)
            elif source == "database":
                series = _try_database(db_path, market)
            elif source == "api":
                series = _try_api(config, market)
            if series is not None and not series.empty:
                logger.info("Loaded '%s' prices from source=%s", market, source)
                break
        if series is None or series.empty:
            raise RuntimeError(f"Could not load prices for market '{market}' from any source")
        if time_index is not None:
            series = prepare_price_series(
                series,
                time_index,
                config.get("forecasting", {}),
                market_name=market,
            )
            forecasted = series.attrs.get("forecasted_timestamps", [])
            if forecasted:
                forecast_index = pd.to_datetime(forecasted)
                forecast_series = series.loc[series.index.isin(forecast_index)]
                _cache_to_db(db_path, market, forecast_series, source="forecast")
        result[market] = series

    return result


def _try_excel(config: dict, market: str) -> pd.Series | None:
    try:
        reader = ExcelReader(config["input_source"]["excel_file"])
        df = reader.read_market_prices()
        if market in df.columns:
            series = df[market].dropna()
            _cache_to_db(config["database"]["path"], market, series, source="excel")
            return series
        return None
    except FileNotFoundError:
        return None


def _try_database(db_path: str, market: str) -> pd.Series | None:
    with get_session(db_path) as session:
        df = load_market_prices(session, market)
    if df.empty:
        return None
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df.set_index("timestamp")["price"]


def _try_api(config: dict, market: str) -> pd.Series | None:
    # Import lazily so Excel-only workflows do not require API dependencies.
    from bess_opt.api.market_api import MarketAPI

    horizon = config["horizon"]
    api = MarketAPI()
    series = api.fetch_prices(market, start=horizon["start"], end=None)
    if config["database"].get("cache_api_results", True):
        _cache_to_db(config["database"]["path"], market, series, source="api")
    return series


def _cache_to_db(db_path: str, market: str, series: pd.Series, source: str) -> None:
    market_type = "energy" if market == "day_ahead" else "reserve"
    with get_session(db_path) as session:
        save_market_prices(session, market, market_type, series, source=source)
