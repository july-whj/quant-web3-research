"""Read public OHLCV data from exchanges supported by CCXT."""

from __future__ import annotations

import ccxt
import pandas as pd


OHLCV_COLUMNS = ["timestamp", "open", "high", "low", "close", "volume"]


def fetch_ohlcv(
    exchange_id: str,
    symbol: str,
    timeframe: str = "1d",
    limit: int = 300,
) -> pd.DataFrame:
    """Fetch public candles and return a UTC-indexed DataFrame.

    This adapter does not accept API credentials and cannot place orders.
    """
    if not 1 <= limit <= 1000:
        raise ValueError("limit must be between 1 and 1000")

    exchange_class = getattr(ccxt, exchange_id, None)
    if exchange_class is None:
        raise ValueError(f"unsupported exchange: {exchange_id}")

    exchange = exchange_class({"enableRateLimit": True})
    rows = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    frame = pd.DataFrame(rows, columns=OHLCV_COLUMNS)
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], unit="ms", utc=True)
    return frame.set_index("timestamp").sort_index()
