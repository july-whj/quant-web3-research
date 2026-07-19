from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import select

from apps.api.app.db import SessionLocal
from apps.api.app.models import MarketCandle, PaperAccount, PaperOrder
from apps.api.app.services.paper_trading import process_open_orders

from .helpers import wallet_login


def seed_minute_candle(
    *,
    close: Decimal = Decimal("50000"),
    low: Decimal | None = None,
    high: Decimal | None = None,
    offset_minutes: int = 0,
) -> None:
    close_time = datetime.now(UTC).replace(microsecond=0) + timedelta(minutes=offset_minutes)
    open_time = close_time - timedelta(minutes=1)
    with SessionLocal() as db:
        db.add(
            MarketCandle(
                exchange="binance",
                symbol="BTC/USDT",
                timeframe="1m",
                open_time=open_time,
                close_time=close_time,
                open=close,
                high=high or close + Decimal("100"),
                low=low or close - Decimal("100"),
                close=close,
                volume=Decimal("10"),
                trade_count=100,
                is_closed=True,
                source="rest",
                received_at=close_time,
            )
        )
        db.commit()


def create_account(client: TestClient, initial_funds: int = 10_000) -> dict:
    response = client.post(
        "/api/v1/paper/accounts",
        json={
            "name": "BTC 模拟账户",
            "exchange": "binance",
            "initial_funds": initial_funds,
            "fee_rate": 0.001,
            "slippage_rate": 0.0005,
            "max_position_pct": 1,
            "max_order_notional": 100_000,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_paper_accounts_require_wallet_login(client: TestClient) -> None:
    assert client.get("/api/v1/paper/accounts").status_code == 401


def test_market_order_updates_paper_funds_position_and_costs(client: TestClient) -> None:
    wallet_login(client)
    seed_minute_candle()
    account = create_account(client)

    response = client.post(
        f"/api/v1/paper/accounts/{account['id']}/orders",
        json={"side": "buy", "order_type": "market", "quantity": "0.01"},
    )

    assert response.status_code == 201, response.text
    order = response.json()
    assert order["status"] == "filled"
    assert Decimal(order["average_price"]) == Decimal("50025.00000000")
    assert Decimal(order["fee_amount"]) > 0
    assert Decimal(order["slippage_amount"]) > 0
    assert Decimal(order["gas_amount"]) == 0

    summary = client.get(f"/api/v1/paper/accounts/{account['id']}").json()
    assert Decimal(summary["position"]["quantity"]) == Decimal("0.01")
    assert Decimal(summary["total_fees"]) > 0
    balances = {balance["asset"]: balance for balance in summary["balances"]}
    assert Decimal(balances["USDT"]["available"]) < Decimal("9500")
    assert Decimal(balances["BTC"]["available"]) == Decimal("0.01")


def test_limit_order_locks_and_releases_paper_funds(client: TestClient) -> None:
    wallet_login(client)
    seed_minute_candle()
    account = create_account(client)

    created = client.post(
        f"/api/v1/paper/accounts/{account['id']}/orders",
        json={
            "side": "buy",
            "order_type": "limit",
            "quantity": "0.01",
            "limit_price": "40000",
        },
    )
    assert created.status_code == 201
    assert created.json()["status"] == "open"
    locked_summary = client.get(f"/api/v1/paper/accounts/{account['id']}").json()
    quote = next(item for item in locked_summary["balances"] if item["asset"] == "USDT")
    assert Decimal(quote["locked"]) > 0

    cancelled = client.delete(
        f"/api/v1/paper/accounts/{account['id']}/orders/{created.json()['id']}"
    )
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"
    final_summary = client.get(f"/api/v1/paper/accounts/{account['id']}").json()
    quote = next(item for item in final_summary["balances"] if item["asset"] == "USDT")
    assert Decimal(quote["locked"]) == 0
    assert Decimal(quote["available"]) == Decimal("10000")


def test_paper_engine_fills_touched_limit_order(client: TestClient) -> None:
    wallet_login(client)
    seed_minute_candle()
    account_payload = create_account(client)
    created = client.post(
        f"/api/v1/paper/accounts/{account_payload['id']}/orders",
        json={
            "side": "buy",
            "order_type": "limit",
            "quantity": "0.01",
            "limit_price": "49000",
        },
    ).json()
    seed_minute_candle(
        close=Decimal("49500"),
        low=Decimal("48000"),
        high=Decimal("50100"),
        offset_minutes=2,
    )
    # The latest candle no longer touches the order. The engine must still
    # replay the previous closed candle after a worker outage.
    seed_minute_candle(
        close=Decimal("52000"),
        low=Decimal("51000"),
        high=Decimal("53000"),
        offset_minutes=3,
    )

    with SessionLocal() as db:
        account = db.get(PaperAccount, account_payload["id"])
        assert account is not None
        assert process_open_orders(db, account) == 1
        db.commit()
        order = db.scalar(select(PaperOrder).where(PaperOrder.id == created["id"]))
        assert order is not None
        assert order.status == "filled"
        assert order.average_price == Decimal("49000")


def test_grid_bot_creates_inventory_and_resting_orders(client: TestClient) -> None:
    wallet_login(client)
    seed_minute_candle()
    account = create_account(client)
    created = client.post(
        f"/api/v1/paper/accounts/{account['id']}/bots",
        json={
            "name": "48K-52K 网格",
            "lower_price": 48000,
            "upper_price": 52000,
            "grid_count": 4,
            "grid_mode": "arithmetic",
            "investment": 4000,
        },
    )
    assert created.status_code == 201, created.text
    started = client.post(
        f"/api/v1/paper/accounts/{account['id']}/bots/{created.json()['id']}/start"
    )
    assert started.status_code == 200, started.text
    assert started.json()["status"] == "running"

    orders = client.get(f"/api/v1/paper/accounts/{account['id']}/orders").json()
    assert any(order["order_type"] == "market" and order["status"] == "filled" for order in orders)
    assert len([order for order in orders if order["status"] == "open"]) == 4
