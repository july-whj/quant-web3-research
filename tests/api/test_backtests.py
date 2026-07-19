from fastapi.testclient import TestClient

from .helpers import wallet_login


def test_authenticated_user_can_run_backtest(client: TestClient) -> None:
    wallet_login(client)
    response = client.post(
        "/api/v1/backtests",
        json={
            "strategy_name": "ma_cross_long_only",
            "symbol": "BTC/USDT",
            "timeframe": "1d",
            "days": 300,
            "parameters": {
                "fast_window": 20,
                "slow_window": 60,
                "fee_rate": 0.001,
                "slippage_rate": 0.0005,
            },
        },
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "succeeded"
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
