"""Minimal JSON-RPC client used by the on-chain examples."""

from __future__ import annotations

from typing import Any

import requests


def rpc_call(
    rpc_url: str,
    method: str,
    params: list[Any] | None = None,
    timeout: float = 15.0,
) -> Any:
    """Call a read-only JSON-RPC method and return its result."""
    if not rpc_url.startswith(("http://", "https://")):
        raise ValueError("rpc_url must start with http:// or https://")

    response = requests.post(
        rpc_url,
        json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params or []},
        timeout=timeout,
    )
    response.raise_for_status()
    payload = response.json()
    if "error" in payload:
        raise RuntimeError(f"RPC error: {payload['error']}")
    return payload.get("result")
