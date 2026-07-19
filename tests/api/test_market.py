from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient

from apps.api.app.db import SessionLocal
from apps.api.app.models import IngestionCheckpoint, MarketCandle

from .helpers import wallet_login


def add_candles(
    *,
    closes: list[str],
    timeframe: str = "1h",
    start: datetime = datetime(2026, 7, 19, tzinfo=UTC),
) -> None:
    with SessionLocal() as db:
        for index, close_value in enumerate(closes):
            open_time = start + timedelta(hours=index)
            close = Decimal(close_value)
            db.add(
                MarketCandle(
                    exchange="binance",
                    symbol="BTC/USDT",
                    timeframe=timeframe,
                    open_time=open_time,
                    close_time=open_time + timedelta(hours=1),
                    open=close,
                    high=close + Decimal("1"),
                    low=close - Decimal("1"),
                    close=close,
                    volume=Decimal("10"),
                    trade_count=100 + index,
                    is_closed=True,
                    source="rest",
                    received_at=open_time + timedelta(hours=1),
                )
            )
        db.commit()


def test_authenticated_user_can_view_market_stream_status(client: TestClient) -> None:
    wallet_login(client)
    open_time = datetime(2026, 7, 19, 12, 0, tzinfo=UTC)
    with SessionLocal() as db:
        db.add(
            IngestionCheckpoint(
                exchange="binance",
                symbol="BTC/USDT",
                timeframe="1m",
                status="live",
                last_closed_open_time=open_time,
            )
        )
        db.add(
            MarketCandle(
                exchange="binance",
                symbol="BTC/USDT",
                timeframe="1m",
                open_time=open_time,
                close_time=open_time + timedelta(minutes=1),
                open=Decimal("60000"),
                high=Decimal("60100"),
                low=Decimal("59900"),
                close=Decimal("60050"),
                volume=Decimal("12.5"),
                is_closed=True,
                source="rest",
                received_at=open_time + timedelta(minutes=1),
            )
        )
        db.commit()

    response = client.get("/api/v1/market/streams")

    assert response.status_code == 200
    assert response.json()[0]["status"] == "live"
    assert response.json()[0]["row_count"] == 1


def test_market_candles_require_authentication(client: TestClient) -> None:
    response = client.get(
        "/api/v1/market/candles",
        params={"exchange": "binance", "symbol": "BTC/USDT", "timeframe": "1h"},
    )

    assert response.status_code == 401


def test_market_candles_are_paginated_oldest_to_newest(client: TestClient) -> None:
    wallet_login(client)
    add_candles(closes=["100", "101", "102", "103", "104"])

    response = client.get(
        "/api/v1/market/candles",
        params={
            "exchange": "binance",
            "symbol": "BTC/USDT",
            "timeframe": "1h",
            "limit": 50,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert [item["close"] for item in payload["items"]] == [
        "100.000000000000",
        "101.000000000000",
        "102.000000000000",
        "103.000000000000",
        "104.000000000000",
    ]
    assert payload["items"][0]["open_time"] < payload["items"][-1]["open_time"]
    assert payload["has_more"] is False
    assert payload["timezone"] == "UTC"


def test_market_candles_support_an_exclusive_before_cursor(client: TestClient) -> None:
    wallet_login(client)
    add_candles(closes=[str(100 + index) for index in range(55)])

    first_response = client.get(
        "/api/v1/market/candles",
        params={"exchange": "binance", "timeframe": "1h", "limit": 50},
    )
    first_payload = first_response.json()
    second_response = client.get(
        "/api/v1/market/candles",
        params={
            "exchange": "binance",
            "timeframe": "1h",
            "limit": 50,
            "before": first_payload["next_before"],
        },
    )

    assert first_payload["has_more"] is True
    assert second_response.status_code == 200
    assert len(second_response.json()["items"]) == 5
    assert second_response.json()["items"][-1]["open_time"] < first_payload["items"][0]["open_time"]


def test_market_signals_use_next_candle_as_execution_time(client: TestClient) -> None:
    wallet_login(client)
    add_candles(closes=["3", "2", "1", "2", "3", "2", "1", "1"])

    response = client.get(
        "/api/v1/market/signals",
        params={
            "exchange": "binance",
            "timeframe": "1h",
            "limit": 50,
            "fast_window": 2,
            "slow_window": 3,
        },
    )

    assert response.status_code == 200
    items = response.json()["items"]
    assert [item["side"] for item in items] == ["buy", "sell"]
    assert items[0]["signal_time"] < items[0]["execution_time"]
    assert items[0]["reason"] == "ma_cross_up"
    assert items[1]["reason"] == "ma_cross_down"


def test_market_signals_validate_ma_windows(client: TestClient) -> None:
    wallet_login(client)
    response = client.get(
        "/api/v1/market/signals",
        params={
            "exchange": "binance",
            "timeframe": "1h",
            "limit": 50,
            "fast_window": 60,
            "slow_window": 20,
        },
    )

    assert response.status_code == 422
