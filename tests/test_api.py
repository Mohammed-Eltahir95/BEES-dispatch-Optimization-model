import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bess_opt.api.market_api import MarketAPI


def test_fetch_prices_parses_response():
    mock_client = MagicMock()
    mock_client.get.return_value = {
        "market": "day_ahead",
        "unit": "EUR/MWh",
        "prices": [
            {"timestamp": "2026-07-05T00:00:00", "price": 30.5},
            {"timestamp": "2026-07-05T01:00:00", "price": 28.1},
        ],
    }
    api = MarketAPI(client=mock_client)
    series = api.fetch_prices("day_ahead", start="2026-07-05T00:00:00", end="2026-07-06T00:00:00")

    assert len(series) == 2
    assert series.iloc[0] == 30.5
    mock_client.get.assert_called_once()


def test_fetch_prices_unknown_market_raises():
    api = MarketAPI(client=MagicMock())
    try:
        api.fetch_prices("unknown_market", start="x", end="y")
        assert False, "expected ValueError"
    except ValueError:
        pass
