from fastapi.testclient import TestClient
from eth_account import Account

from .helpers import wallet_login


def test_wallet_signature_login_creates_session(client: TestClient) -> None:
    account, challenge, verify_response = wallet_login(client)

    assert verify_response.json()["address"] == account.address
    assert "qwr_session" in verify_response.cookies

    me_response = client.get("/api/v1/auth/me")
    assert me_response.status_code == 200
    assert me_response.json()["chain_id"] == 56

    replay_response = client.post(
        "/api/v1/auth/verify",
        json={
            "address": account.address,
            "message": challenge["message"],
            "signature": "0x" + "00" * 65,
        },
    )
    assert replay_response.status_code == 401


def test_usage_metrics_are_admin_only(client: TestClient) -> None:
    wallet_login(client)
    assert client.get("/api/v1/analytics/usage").status_code == 403

    response = client.get(
        "/api/v1/analytics/usage",
        headers={"X-Admin-Key": "test-admin-key"},
    )
    assert response.status_code == 200
    assert response.json() == {
        "users": 1,
        "wallets": 1,
        "daily_active_users": 1,
        "monthly_active_users": 1,
    }


def test_same_evm_address_on_testnet_reuses_user(client: TestClient) -> None:
    account = Account.create()
    wallet_login(client, account=account, chain_id=56)
    client.post("/api/v1/auth/logout")
    wallet_login(client, account=account, chain_id=97)

    response = client.get(
        "/api/v1/analytics/usage",
        headers={"X-Admin-Key": "test-admin-key"},
    )
    assert response.status_code == 200
    assert response.json()["users"] == 1
    assert response.json()["wallets"] == 2
