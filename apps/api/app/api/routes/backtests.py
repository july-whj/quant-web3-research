from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...core.config import Settings, get_settings
from ...db.session import get_db
from ...models import BacktestRun, User, UserSession, UserWallet
from ...schemas.research import BacktestCreate, BacktestResponse
from ...services.backtests import create_and_dispatch_backtest
from ..dependencies import get_current_identity


router = APIRouter(prefix="/backtests", tags=["backtests"])


@router.get("", response_model=list[BacktestResponse])
def list_backtests(
    db: Session = Depends(get_db),
    identity: tuple[User, UserWallet, UserSession] = Depends(get_current_identity),
) -> list[BacktestRun]:
    user, _, _ = identity
    statement = (
        select(BacktestRun)
        .where(BacktestRun.owner_id == user.id)
        .order_by(BacktestRun.created_at.desc())
        .limit(100)
    )
    return list(db.scalars(statement).all())


@router.post("", response_model=BacktestResponse, status_code=status.HTTP_201_CREATED)
def create_backtest(
    payload: BacktestCreate,
    db: Session = Depends(get_db),
    identity: tuple[User, UserWallet, UserSession] = Depends(get_current_identity),
    settings: Settings = Depends(get_settings),
) -> BacktestRun:
    user, _, _ = identity
    return create_and_dispatch_backtest(
        db,
        owner_id=user.id,
        payload=payload,
        settings=settings,
    )


@router.get("/{run_id}", response_model=BacktestResponse)
def get_backtest(
    run_id: str,
    db: Session = Depends(get_db),
    identity: tuple[User, UserWallet, UserSession] = Depends(get_current_identity),
) -> BacktestRun:
    user, _, _ = identity
    run = db.scalar(
        select(BacktestRun).where(BacktestRun.id == run_id, BacktestRun.owner_id == user.id)
    )
    if run is None:
        raise HTTPException(status_code=404, detail="回测任务不存在")
    return run
