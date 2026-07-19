from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import select

from apps.api.app.db import SessionLocal
from apps.api.app.models import MarketCandle

from .helpers import wallet_login


def seed_daily_candles(count: int = 301) -> None:
    end = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    start = end - timedelta(days=count - 1)
    with SessionLocal() as db:
        for index in range(count):
            open_time = start + timedelta(days=index)
            close = Decimal(50_000 + index * 10)
            db.add(
                MarketCandle(
                    exchange="binance",
                    symbol="BTC/USDT",
                    timeframe="1d",
                    open_time=open_time,
                    close_time=open_time + timedelta(days=1),
                    open=close - Decimal("5"),
                    high=close + Decimal("10"),
                    low=close - Decimal("15"),
                    close=close,
                    volume=Decimal("100"),
                    trade_count=1000 + index,
                    is_closed=True,
                    source="rest",
                    received_at=open_time + timedelta(days=1),
                )
            )
        db.commit()


def test_authenticated_user_can_run_backtest(client: TestClient) -> None:
    wallet_login(client)
    seed_daily_candles()
    response = client.post(
        "/api/v1/backtests",
        json={
            "strategy_name": "ma_cross_long_only",
            "strategy_version": "1.0.0",
            "exchange": "binance",
            "symbol": "BTC/USDT",
            "timeframe": "1d",
            "days": 300,
            "parameters": {
                "fast_window": 20,
                "slow_window": 60,
            },
            "execution": {
                "initial_capital": 1000,
                "fee_rate": 0.001,
                "slippage_rate": 0.0005,
                "signal_on": "candle_close",
                "execute_on": "next_candle_open",
            },
        },
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "succeeded"
    assert payload["strategy_version"] == "1.0.0"
    assert payload["exchange"] == "binance"
    assert payload["parameters"] == {"fast_window": 20, "slow_window": 60}
    assert payload["execution_config"]["fee_rate"] == 0.001
    assert payload["data_snapshot"]["candle_count"] == 301
    assert payload["data_snapshot"]["expected_candle_count"] == 301
    assert payload["data_snapshot"]["gap_count"] == 0
    assert payload["data_snapshot"]["closed_candles_only"] is True
    assert "strategy_total_return" in payload["summary"]
    assert "strategy_max_drawdown" in payload["summary"]


def test_rejects_invalid_moving_average_windows(client: TestClient) -> None:
    wallet_login(client)
    response = client.post(
        "/api/v1/backtests",
        json={
            "strategy_name": "ma_cross_long_only",
            "symbol": "BTC/USDT",
            "timeframe": "1d",
            "days": 300,
            "parameters": {"fast_window": 60, "slow_window": 20},
        },
    )
    assert response.status_code == 422


def test_rejects_backtest_when_market_data_is_missing(client: TestClient) -> None:
    wallet_login(client)
    response = client.post(
        "/api/v1/backtests",
        json={
            "strategy_name": "ma_cross_long_only",
            "exchange": "okx",
            "symbol": "BTC/USDT",
            "timeframe": "1d",
            "days": 300,
            "parameters": {"fast_window": 20, "slow_window": 60},
        },
    )

    assert response.status_code == 422
    assert "没有可用于回测" in response.json()["detail"]


def test_strategy_catalog_is_generated_from_registry(client: TestClient) -> None:
    response = client.get("/api/v1/strategies")

    assert response.status_code == 200
    definition = next(
        item for item in response.json() if item["key"] == "ma_cross_long_only"
    )
    assert definition["key"] == "ma_cross_long_only"
    assert definition["version"] == "1.0.0"
    assert definition["default_warmup_bars"] == 60
    assert set(definition["parameters_schema"]["properties"]) == {
        "fast_window",
        "slow_window",
    }


def test_rejects_backtest_when_requested_range_has_a_gap(client: TestClient) -> None:
    wallet_login(client)
    seed_daily_candles()
    with SessionLocal() as db:
        missing = db.scalar(
            select(MarketCandle)
            .where(MarketCandle.exchange == "binance", MarketCandle.timeframe == "1d")
            .order_by(MarketCandle.open_time.asc())
            .offset(100)
        )
        assert missing is not None
        db.delete(missing)
        db.commit()

    response = client.post(
        "/api/v1/backtests",
        json={
            "strategy_name": "ma_cross_long_only",
            "exchange": "binance",
            "symbol": "BTC/USDT",
            "timeframe": "1d",
            "days": 300,
            "parameters": {"fast_window": 20, "slow_window": 60},
        },
    )

    assert response.status_code == 422
    assert "缺少 1 根 K 线" in response.json()["detail"]
