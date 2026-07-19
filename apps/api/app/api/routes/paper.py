from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...db.session import get_db
from ...models import (
    PaperAccount,
    PaperAccountSnapshot,
    PaperBot,
    PaperFill,
    PaperLedgerEntry,
    PaperOrder,
    User,
    UserSession,
    UserWallet,
)
from ...schemas.paper import (
    PaperAccountCreate,
    PaperAccountResponse,
    PaperBotResponse,
    PaperFillResponse,
    PaperFundsCreate,
    PaperGridCreate,
    PaperLedgerResponse,
    PaperOrderCreate,
    PaperOrderResponse,
    PaperSnapshotResponse,
)
from ...services.paper_trading import (
    PaperTradingError,
    account_response,
    add_paper_funds,
    cancel_order,
    change_grid_bot_status,
    create_account,
    create_grid_bot,
    owned_account,
    place_order,
)
from ..dependencies import get_current_identity


router = APIRouter(prefix="/paper", tags=["paper-trading"])


def _paper_error(db: Session, exc: PaperTradingError) -> None:
    db.commit()
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail=str(exc),
    ) from exc


@router.get("/accounts", response_model=list[PaperAccountResponse])
def list_accounts(
    db: Session = Depends(get_db),
    identity: tuple[User, UserWallet, UserSession] = Depends(get_current_identity),
) -> list[PaperAccountResponse]:
    user, _, _ = identity
    accounts = list(
        db.scalars(
            select(PaperAccount)
            .where(PaperAccount.owner_id == user.id)
            .order_by(PaperAccount.created_at.desc())
        ).all()
    )
    return [account_response(db, account) for account in accounts]


@router.post(
    "/accounts",
    response_model=PaperAccountResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_paper_account(
    payload: PaperAccountCreate,
    db: Session = Depends(get_db),
    identity: tuple[User, UserWallet, UserSession] = Depends(get_current_identity),
) -> PaperAccountResponse:
    user, _, _ = identity
    account = create_account(db, owner_id=user.id, payload=payload)
    db.commit()
    db.refresh(account)
    return account_response(db, account)


@router.get("/accounts/{account_id}", response_model=PaperAccountResponse)
def get_paper_account(
    account_id: str,
    db: Session = Depends(get_db),
    identity: tuple[User, UserWallet, UserSession] = Depends(get_current_identity),
) -> PaperAccountResponse:
    user, _, _ = identity
    try:
        account = owned_account(db, account_id, user.id)
    except PaperTradingError as exc:
        _paper_error(db, exc)
    return account_response(db, account)


@router.post("/accounts/{account_id}/funds", response_model=PaperAccountResponse)
def deposit_paper_funds(
    account_id: str,
    payload: PaperFundsCreate,
    db: Session = Depends(get_db),
    identity: tuple[User, UserWallet, UserSession] = Depends(get_current_identity),
) -> PaperAccountResponse:
    user, _, _ = identity
    try:
        account = owned_account(db, account_id, user.id, lock=True)
        add_paper_funds(db, account=account, payload=payload)
        db.commit()
        db.refresh(account)
    except PaperTradingError as exc:
        _paper_error(db, exc)
    return account_response(db, account)


@router.get("/accounts/{account_id}/orders", response_model=list[PaperOrderResponse])
def list_paper_orders(
    account_id: str,
    order_status: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    identity: tuple[User, UserWallet, UserSession] = Depends(get_current_identity),
) -> list[PaperOrder]:
    user, _, _ = identity
    try:
        account = owned_account(db, account_id, user.id)
    except PaperTradingError as exc:
        _paper_error(db, exc)
    statement = select(PaperOrder).where(PaperOrder.account_id == account.id)
    if order_status:
        statement = statement.where(PaperOrder.status == order_status)
    return list(
        db.scalars(statement.order_by(PaperOrder.created_at.desc()).limit(limit)).all()
    )


@router.post(
    "/accounts/{account_id}/orders",
    response_model=PaperOrderResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_paper_order(
    account_id: str,
    payload: PaperOrderCreate,
    db: Session = Depends(get_db),
    identity: tuple[User, UserWallet, UserSession] = Depends(get_current_identity),
) -> PaperOrder:
    user, _, _ = identity
    try:
        account = owned_account(db, account_id, user.id, lock=True)
        order = place_order(
            db,
            account=account,
            side=payload.side,
            order_type=payload.order_type,
            quantity=payload.quantity,
            limit_price=payload.limit_price,
            client_order_id=payload.client_order_id,
        )
        db.commit()
        db.refresh(order)
        return order
    except PaperTradingError as exc:
        _paper_error(db, exc)


@router.delete("/accounts/{account_id}/orders/{order_id}", response_model=PaperOrderResponse)
def cancel_paper_order(
    account_id: str,
    order_id: str,
    db: Session = Depends(get_db),
    identity: tuple[User, UserWallet, UserSession] = Depends(get_current_identity),
) -> PaperOrder:
    user, _, _ = identity
    try:
        account = owned_account(db, account_id, user.id, lock=True)
        order = cancel_order(db, account=account, order_id=order_id)
        db.commit()
        db.refresh(order)
        return order
    except PaperTradingError as exc:
        _paper_error(db, exc)


@router.get("/accounts/{account_id}/fills", response_model=list[PaperFillResponse])
def list_paper_fills(
    account_id: str,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    identity: tuple[User, UserWallet, UserSession] = Depends(get_current_identity),
) -> list[PaperFill]:
    user, _, _ = identity
    try:
        account = owned_account(db, account_id, user.id)
    except PaperTradingError as exc:
        _paper_error(db, exc)
    return list(
        db.scalars(
            select(PaperFill)
            .where(PaperFill.account_id == account.id)
            .order_by(PaperFill.created_at.desc())
            .limit(limit)
        ).all()
    )


@router.get("/accounts/{account_id}/ledger", response_model=list[PaperLedgerResponse])
def list_paper_ledger(
    account_id: str,
    limit: int = Query(default=200, ge=1, le=1000),
    db: Session = Depends(get_db),
    identity: tuple[User, UserWallet, UserSession] = Depends(get_current_identity),
) -> list[PaperLedgerEntry]:
    user, _, _ = identity
    try:
        account = owned_account(db, account_id, user.id)
    except PaperTradingError as exc:
        _paper_error(db, exc)
    return list(
        db.scalars(
            select(PaperLedgerEntry)
            .where(PaperLedgerEntry.account_id == account.id)
            .order_by(PaperLedgerEntry.created_at.desc())
            .limit(limit)
        ).all()
    )


@router.get("/accounts/{account_id}/snapshots", response_model=list[PaperSnapshotResponse])
def list_paper_snapshots(
    account_id: str,
    limit: int = Query(default=300, ge=1, le=1000),
    db: Session = Depends(get_db),
    identity: tuple[User, UserWallet, UserSession] = Depends(get_current_identity),
) -> list[PaperAccountSnapshot]:
    user, _, _ = identity
    try:
        account = owned_account(db, account_id, user.id)
    except PaperTradingError as exc:
        _paper_error(db, exc)
    rows = list(
        db.scalars(
            select(PaperAccountSnapshot)
            .where(PaperAccountSnapshot.account_id == account.id)
            .order_by(PaperAccountSnapshot.market_time.desc())
            .limit(limit)
        ).all()
    )
    return list(reversed(rows))


@router.get("/accounts/{account_id}/bots", response_model=list[PaperBotResponse])
def list_paper_bots(
    account_id: str,
    db: Session = Depends(get_db),
    identity: tuple[User, UserWallet, UserSession] = Depends(get_current_identity),
) -> list[PaperBot]:
    user, _, _ = identity
    try:
        account = owned_account(db, account_id, user.id)
    except PaperTradingError as exc:
        _paper_error(db, exc)
    return list(
        db.scalars(
            select(PaperBot)
            .where(PaperBot.account_id == account.id)
            .order_by(PaperBot.created_at.desc())
        ).all()
    )


@router.post(
    "/accounts/{account_id}/bots",
    response_model=PaperBotResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_paper_bot(
    account_id: str,
    payload: PaperGridCreate,
    db: Session = Depends(get_db),
    identity: tuple[User, UserWallet, UserSession] = Depends(get_current_identity),
) -> PaperBot:
    user, _, _ = identity
    try:
        account = owned_account(db, account_id, user.id, lock=True)
        bot = create_grid_bot(db, account=account, payload=payload)
        db.commit()
        db.refresh(bot)
        return bot
    except PaperTradingError as exc:
        _paper_error(db, exc)


@router.post(
    "/accounts/{account_id}/bots/{bot_id}/{action}",
    response_model=PaperBotResponse,
)
def control_paper_bot(
    account_id: str,
    bot_id: str,
    action: Literal["start", "pause", "stop"],
    db: Session = Depends(get_db),
    identity: tuple[User, UserWallet, UserSession] = Depends(get_current_identity),
) -> PaperBot:
    user, _, _ = identity
    try:
        account = owned_account(db, account_id, user.id, lock=True)
        bot = db.scalar(
            select(PaperBot)
            .where(PaperBot.id == bot_id, PaperBot.account_id == account.id)
            .with_for_update()
        )
        if bot is None:
            raise PaperTradingError("网格机器人不存在")
        bot = change_grid_bot_status(db, account=account, bot=bot, action=action)
        db.commit()
        db.refresh(bot)
        return bot
    except PaperTradingError as exc:
        _paper_error(db, exc)
