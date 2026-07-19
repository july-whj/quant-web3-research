from __future__ import annotations

import hashlib
import secrets


def hash_value(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def new_nonce() -> str:
    # EIP-4361 requires at least 8 alphanumeric characters.
    return secrets.token_hex(12)


def new_session_token() -> str:
    return secrets.token_urlsafe(48)
