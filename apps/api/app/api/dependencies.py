from __future__ import annotations

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from ..core.config import Settings, get_settings
from ..db.session import get_db
from ..models import User, UserSession, UserWallet
from ..services.auth import session_from_token


def get_current_identity(
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> tuple[User, UserWallet, UserSession]:
    identity = session_from_token(db, request.cookies.get(settings.session_cookie_name))
    if identity is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="请先使用钱包登录")
    return identity


def require_admin_key(
    x_admin_key: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> None:
    if not x_admin_key or x_admin_key != settings.admin_api_key:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="管理员密钥无效")
