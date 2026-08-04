"""Pydantic models for validating API request/response payloads."""
from __future__ import annotations

from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


class PricePoint(BaseModel):
    timestamp: datetime
    price: float


class MarketPriceResponse(BaseModel):
    market: str
    unit: str = "EUR/MWh"
    prices: List[PricePoint]


class BidRequest(BaseModel):
    market: str
    timestamp: datetime
    power_mw: float = Field(..., description="Positive = discharge/sell, negative = charge/buy")
    price_limit: float


class BidResponse(BaseModel):
    bid_id: str
    status: str
    accepted_power_mw: float | None = None
