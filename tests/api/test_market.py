from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient

from apps.api.app.db import SessionLocal
from apps.api.app.models import IngestionCheckpoint, MarketCandle

from .helpers import wallet_login


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
