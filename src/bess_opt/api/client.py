"""Base HTTP client: auth headers, retries/backoff, rate limiting."""
from __future__ import annotations

import os
import time
from typing import Any, Dict, Optional

import requests
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential

from bess_opt.utils.logger import get_logger
from bess_opt.utils.helpers import load_yaml

load_dotenv()
logger = get_logger(__name__)


class APIClient:
    def __init__(self, config_path: str = "config/api_config.yaml"):
        self.config = load_yaml(config_path)
        self.base_url = os.getenv(self.config["base_url_env"], "")
        self.api_key = os.getenv(self.config["api_key_env"], "")
        self.timeout = self.config.get("timeout_seconds", 15)
        self.max_retries = self.config.get("max_retries", 3)
        self._min_interval = 60.0 / self.config.get("rate_limit", {}).get(
            "max_requests_per_minute", 60
        )
        self._last_call_ts = 0.0

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _throttle(self):
        elapsed = time.time() - self._last_call_ts
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    def get(self, endpoint_key: str, params: Optional[Dict[str, Any]] = None) -> Dict:
        self._throttle()
        url = self.base_url + self.config["endpoints"][endpoint_key]
        logger.info("GET %s params=%s", url, params)
        resp = requests.get(url, headers=self._headers(), params=params, timeout=self.timeout)
        self._last_call_ts = time.time()
        resp.raise_for_status()
        return resp.json()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    def post(self, endpoint_key: str, payload: Dict[str, Any]) -> Dict:
        self._throttle()
        url = self.base_url + self.config["endpoints"][endpoint_key]
        logger.info("POST %s payload=%s", url, payload)
        resp = requests.post(url, headers=self._headers(), json=payload, timeout=self.timeout)
        self._last_call_ts = time.time()
        resp.raise_for_status()
        return resp.json()
