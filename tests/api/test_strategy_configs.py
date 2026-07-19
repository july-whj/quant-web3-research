from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient

from apps.api.app.db import SessionLocal
from apps.api.app.models import MarketCandle

from .helpers import wallet_login


def seed_daily_candles(count: int = 301) -> None:
    end = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    start = end - timedelta(days=count - 1)
    with SessionLocal() as db:
        for index in range(count):
            open_time = start + timedelta(days=index)
            wave = Decimal((index % 40) - 20) * Decimal("150")
            close = Decimal(50_000 + index * 10) + wave
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


def config_payload(*, fast_window: int = 20, slow_window: int = 60) -> dict:
    return {
        "name": "BTC 日线双均线",
        "strategy_name": "ma_cross_long_only",
        "strategy_version": "1.0.0",
        "exchange": "binance",
        "symbol": "BTC/USDT",
        "timeframe": "1d",
        "days": 300,
        "parameters": {
            "fast_window": fast_window,
            "slow_window": slow_window,
        },
        "risk": {"max_position_pct": 0.5},
        "execution": {
            "initial_capital": 1000,
            "fee_rate": 0.001,
            "slippage_rate": 0.0005,
            "signal_on": "candle_close",
            "execute_on": "next_candle_open",
        },
    }


def test_strategy_configs_require_authentication(client: TestClient) -> None:
    assert client.get("/api/v1/strategy-configs").status_code == 401


def test_config_versions_are_immutable_and_can_start_linked_backtests(
    client: TestClient,
) -> None:
    wallet_login(client)
    seed_daily_candles()

    created = client.post("/api/v1/strategy-configs", json=config_payload())
    assert created.status_code == 201
    config = created.json()
    assert config["latest_version_number"] == 1
    assert config["versions"][0]["parameters"] == {
        "fast_window": 20,
        "slow_window": 60,
    }

    version_payload = config_payload(fast_window=10, slow_window=30)
    version_payload.pop("name")
    updated = client.post(
        f"/api/v1/strategy-configs/{config['id']}/versions",
        json=version_payload,
    )
    assert updated.status_code == 201
    versions = updated.json()["versions"]
    assert [version["version_number"] for version in versions] == [2, 1]
    assert versions[0]["parameters"] == {"fast_window": 10, "slow_window": 30}
    assert versions[1]["parameters"] == {"fast_window": 20, "slow_window": 60}

    run = client.post(
        f"/api/v1/strategy-configs/{config['id']}/backtests",
        json={"version_number": 1},
    )
    assert run.status_code == 201
    assert run.json()["status"] == "succeeded"
    assert run.json()["strategy_config_version_id"] == versions[1]["id"]
    assert run.json()["risk_config"] == {"max_position_pct": 0.5}


def test_all_registered_strategies_have_generic_previews(client: TestClient) -> None:
    wallet_login(client)
    seed_daily_candles()
    definitions = client.get("/api/v1/strategies").json()

    for definition in definitions:
        parameters = {
            name: schema["default"]
            for name, schema in definition["parameters_schema"]["properties"].items()
        }
        response = client.post(
            f"/api/v1/strategies/{definition['key']}/preview",
            json={
                "strategy_version": definition["version"],
                "exchange": "binance",
                "symbol": "BTC/USDT",
                "timeframe": "1d",
                "limit": 200,
                "parameters": parameters,
            },
        )
        assert response.status_code == 200, (definition["key"], response.text)
        preview = response.json()
        assert preview["strategy_name"] == definition["key"]
        assert len(preview["candles"]) == 200
        assert {plot["key"] for plot in preview["plots"]} == {
            plot["key"] for plot in definition["plots"]
        }
        assert preview["explanation"]
