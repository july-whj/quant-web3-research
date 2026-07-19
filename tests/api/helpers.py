from eth_account import Account
from eth_account.messages import encode_defunct
from fastapi.testclient import TestClient


def wallet_login(client: TestClient, account=None, chain_id: int = 56):
    account = account or Account.create()
    challenge_response = client.post(
        "/api/v1/auth/nonce",
        json={"address": account.address, "chain_id": chain_id},
    )
    assert challenge_response.status_code == 201
    challenge = challenge_response.json()
    signed = Account.sign_message(encode_defunct(text=challenge["message"]), account.key)
    verify_response = client.post(
        "/api/v1/auth/verify",
        json={
            "address": account.address,
            "message": challenge["message"],
            "signature": signed.signature.hex(),
        },
    )
    assert verify_response.status_code == 200
    return account, challenge, verify_response
