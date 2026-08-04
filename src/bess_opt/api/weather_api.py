"""Optional: ambient temperature forecast, used as a calendar-aging input."""
from __future__ import annotations

import pandas as pd

from bess_opt.api.client import APIClient


class WeatherAPI:
    def __init__(self, client: APIClient | None = None):
        self.client = client or APIClient()

    def fetch_temperature(self, start: str, end: str, location: str) -> pd.Series:
        raw = self.client.get(
            "weather_forecast", params={"start": start, "end": end, "location": location}
        )
        series = pd.Series(
            {p["timestamp"]: p["temp_c"] for p in raw["forecast"]}, name="temp_c"
        ).sort_index()
        return series
