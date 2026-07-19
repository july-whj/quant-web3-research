from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from ...core.config import Settings, get_settings
from ...core.security import hash_value
from ...db.session import get_db
from ...models import User, UserSession, UserWallet
from ...schemas.auth import (
    AuthChallengeResponse,
    CurrentUserResponse,
    NonceRequest,
    VerifyRequest,
)
from ...services.auth import issue_challenge, verify_challenge
from ..dependencies import get_current_identity


router = APIRouter(prefix="/auth", tags=["auth"])


def current_user_response(user: User, wallet: UserWallet) -> CurrentUserResponse:
    return CurrentUserResponse(
        id=user.id,
        address=wallet.address,
        chain_id=wallet.chain_id,
        created_at=user.created_at,
        last_login_at=user.last_login_at,
    )


@router.post("/nonce", response_model=AuthChallengeResponse, status_code=201)
def create_nonce(
    payload: NonceRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> AuthChallengeResponse:
    challenge = issue_challenge(db, payload.address, payload.chain_id, settings)
    return AuthChallengeResponse(
        address=challenge.address,
        chain_id=challenge.chain_id,
        message=challenge.message,
        expires_at=challenge.expires_at,
    )


@router.post("/verify", response_model=CurrentUserResponse)
def verify(
    payload: VerifyRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> CurrentUserResponse:
    user, wallet, token = verify_challenge(
        db,
        address=payload.address,
        message=payload.message,
        signature=payload.signature,
        request=request,
        settings=settings,
    )
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        max_age=settings.session_ttl_hours * 3600,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
        path="/",
    )
    return current_user_response(user, wallet)


@router.get("/me", response_model=CurrentUserResponse)
def me(
    identity: tuple[User, UserWallet, UserSession] = Depends(get_current_identity),
) -> CurrentUserResponse:
    user, wallet, _ = identity
    return current_user_response(user, wallet)


@router.post("/logout", status_code=204)
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> Response:
    token = request.cookies.get(settings.session_cookie_name)
    if token:
        session = db.query(UserSession).filter(UserSession.token_hash == hash_value(token)).first()
        if session and session.revoked_at is None:
            session.revoked_at = datetime.now(UTC)
            db.commit()
    response.delete_cookie(settings.session_cookie_name, path="/")
    return response
