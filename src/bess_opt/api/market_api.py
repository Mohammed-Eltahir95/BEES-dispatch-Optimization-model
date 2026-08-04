"""Market data fetch + bid submission, built on top of APIClient."""
from __future__ import annotations

import pandas as pd

from bess_opt.api.client import APIClient
from bess_opt.api.schemas import MarketPriceResponse, BidRequest, BidResponse
from bess_opt.utils.logger import get_logger

logger = get_logger(__name__)

_ENDPOINT_MAP = {
    "day_ahead": "day_ahead_prices",
    "fcr": "fcr_prices",
    "afrr": "afrr_prices",
}


class MarketAPI:
    def __init__(self, client: APIClient | None = None):
        self.client = client or APIClient()

    def fetch_prices(self, market: str, start: str, end: str) -> pd.Series:
        endpoint_key = _ENDPOINT_MAP.get(market)
        if endpoint_key is None:
            raise ValueError(f"Unknown market '{market}'")

        raw = self.client.get(endpoint_key, params={"start": start, "end": end})
        parsed = MarketPriceResponse(**raw)
        series = pd.Series(
            {p.timestamp: p.price for p in parsed.prices}, name=market
        ).sort_index()
        logger.info("Fetched %d price points for %s", len(series), market)
        return series

    def submit_bid(self, market: str, timestamp: str, power_mw: float,
                    price_limit: float) -> BidResponse:
        req = BidRequest(
            market=market, timestamp=timestamp,
            power_mw=power_mw, price_limit=price_limit,
        )
        raw = self.client.post("submit_bid", req.model_dump(mode="json"))
        return BidResponse(**raw)
