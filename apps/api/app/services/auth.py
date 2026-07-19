from __future__ import annotations

from datetime import UTC, datetime, timedelta

from eth_account import Account
from eth_account.messages import encode_defunct
from eth_utils import is_address, to_checksum_address
from fastapi import HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.config import Settings
from ..core.security import hash_value, new_nonce, new_session_token
from ..models import AuthChallenge, LoginEvent, User, UserSession, UserWallet


def now_utc() -> datetime:
    return datetime.now(UTC)


def normalize_address(address: str) -> str:
    if not is_address(address):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="无效的钱包地址")
    return to_checksum_address(address)


def build_siwe_message(
    *, address: str, chain_id: int, nonce: str, issued_at: datetime, expires_at: datetime, settings: Settings
) -> str:
    return (
        f"{settings.siwe_domain} wants you to sign in with your Ethereum account:\n"
        f"{address}\n\n"
        f"{settings.siwe_statement}\n\n"
        f"URI: {settings.siwe_uri}\n"
        "Version: 1\n"
        f"Chain ID: {chain_id}\n"
        f"Nonce: {nonce}\n"
        f"Issued At: {issued_at.isoformat().replace('+00:00', 'Z')}\n"
        f"Expiration Time: {expires_at.isoformat().replace('+00:00', 'Z')}"
    )


def issue_challenge(db: Session, address: str, chain_id: int, settings: Settings) -> AuthChallenge:
    normalized = normalize_address(address)
    if chain_id not in settings.allowed_chain_id_set:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="当前网络暂不支持登录")
    issued_at = now_utc()
    expires_at = issued_at + timedelta(seconds=settings.challenge_ttl_seconds)
    nonce = new_nonce()
    message = build_siwe_message(
        address=normalized,
        chain_id=chain_id,
        nonce=nonce,
        issued_at=issued_at,
        expires_at=expires_at,
        settings=settings,
    )
    challenge = AuthChallenge(
        address=normalized,
        chain_id=chain_id,
        nonce=nonce,
        message=message,
        message_hash=hash_value(message),
        expires_at=expires_at,
    )
    db.add(challenge)
    db.commit()
    db.refresh(challenge)
    return challenge


def verify_challenge(
    db: Session,
    *,
    address: str,
    message: str,
    signature: str,
    request: Request,
    settings: Settings,
) -> tuple[User, UserWallet, str]:
    normalized = normalize_address(address)
    challenge = db.scalar(
        select(AuthChallenge)
        .where(
            AuthChallenge.address == normalized,
            AuthChallenge.message_hash == hash_value(message),
            AuthChallenge.used_at.is_(None),
        )
        .with_for_update()
    )
    if challenge is None or challenge.message != message:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录消息无效或已经使用")
    expires_at = challenge.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if expires_at <= now_utc():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录消息已经过期")

    try:
        recovered = Account.recover_message(encode_defunct(text=message), signature=signature)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="钱包签名格式无效") from exc
    if to_checksum_address(recovered) != normalized:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="钱包签名与地址不匹配")

    wallet = db.scalar(
        select(UserWallet).where(
            UserWallet.address == normalized,
            UserWallet.chain_id == challenge.chain_id,
        )
    )
    current_time = now_utc()
    if wallet is None:
        existing_wallet = db.scalar(
            select(UserWallet)
            .where(UserWallet.address == normalized)
            .order_by(UserWallet.created_at.asc())
        )
        if existing_wallet is None:
            user = User(last_login_at=current_time)
            db.add(user)
            db.flush()
        else:
            user = db.get(User, existing_wallet.user_id)
            if user is None or not user.is_active:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="研究账户不可用")
            user.last_login_at = current_time
        wallet = UserWallet(user_id=user.id, address=normalized, chain_id=challenge.chain_id)
        db.add(wallet)
    else:
        user = db.get(User, wallet.user_id)
        if user is None or not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="研究账户不可用")
        user.last_login_at = current_time

    challenge.used_at = current_time
    token = new_session_token()
    db.add(
        UserSession(
            user_id=user.id,
            token_hash=hash_value(token),
            expires_at=current_time + timedelta(hours=settings.session_ttl_hours),
        )
    )
    client_host = request.client.host if request.client else None
    db.add(
        LoginEvent(
            user_id=user.id,
            wallet_address=normalized,
            chain_id=challenge.chain_id,
            ip_hash=hash_value(client_host) if client_host else None,
        )
    )
    db.commit()
    db.refresh(user)
    db.refresh(wallet)
    return user, wallet, token


def session_from_token(db: Session, token: str | None) -> tuple[User, UserWallet, UserSession] | None:
    if not token:
        return None
    session = db.scalar(
        select(UserSession).where(
            UserSession.token_hash == hash_value(token),
            UserSession.revoked_at.is_(None),
        )
    )
    if session is None:
        return None
    expires_at = session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if expires_at <= now_utc():
        return None
    user = db.get(User, session.user_id)
    wallet = db.scalar(
        select(UserWallet)
        .where(UserWallet.user_id == session.user_id)
        .order_by(UserWallet.is_primary.desc(), UserWallet.created_at.asc())
    )
    if user is None or wallet is None or not user.is_active:
        return None
    return user, wallet, session
