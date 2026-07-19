from datetime import UTC, datetime
from decimal import Decimal

from apps.collector.quant_web3_collector.exchanges import (
    parse_binance_message,
    parse_okx_message,
)


def test_parse_closed_binance_candle() -> None:
    candle = parse_binance_message(
        {
            "e": "kline",
            "E": 1_720_000_060_000,
            "k": {
                "t": 1_720_000_000_000,
                "T": 1_720_000_059_999,
                "i": "1m",
                "o": "60000.0",
                "h": "60100.0",
                "l": "59900.0",
                "c": "60050.0",
                "v": "12.5",
                "n": 42,
                "x": True,
            },
        },
        received_at=datetime(2026, 7, 19, tzinfo=UTC),
    )

    assert candle is not None
    assert candle.exchange == "binance"
    assert candle.timeframe == "1m"
    assert candle.close == Decimal("60050.0")
    assert candle.trade_count == 42


def test_ignore_open_binance_candle() -> None:
    assert parse_binance_message({"e": "kline", "k": {"x": False}}) is None


def test_parse_only_confirmed_okx_candles() -> None:
    candles = parse_okx_message(
        {
            "arg": {"channel": "candle1H", "instId": "BTC-USDT"},
            "data": [
                ["1720000000000", "60000", "60100", "59900", "60050", "10", "0", "0", "1"],
                ["1720003600000", "60050", "60200", "60000", "60100", "8", "0", "0", "0"],
            ],
        },
        received_at=datetime(2026, 7, 19, tzinfo=UTC),
    )

    assert len(candles) == 1
    assert candles[0].exchange == "okx"
    assert candles[0].timeframe == "1h"
    assert candles[0].volume == Decimal("10")
