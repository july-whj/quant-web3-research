from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ...db.session import get_db
from ...models import IngestionCheckpoint, MarketCandle, User, UserSession, UserWallet
from ...schemas.research import MarketStreamResponse
from ..dependencies import get_current_identity


router = APIRouter(prefix="/market", tags=["market data"])


@router.get("/streams", response_model=list[MarketStreamResponse])
def list_market_streams(
    db: Session = Depends(get_db),
    _: tuple[User, UserWallet, UserSession] = Depends(get_current_identity),
) -> list[MarketStreamResponse]:
    checkpoints = list(
        db.scalars(
            select(IngestionCheckpoint).order_by(
                IngestionCheckpoint.exchange,
                IngestionCheckpoint.timeframe,
            )
        ).all()
    )
    responses: list[MarketStreamResponse] = []
    for checkpoint in checkpoints:
        candle_count = db.scalar(
            select(func.count(MarketCandle.id)).where(
                MarketCandle.exchange == checkpoint.exchange,
                MarketCandle.symbol == checkpoint.symbol,
                MarketCandle.timeframe == checkpoint.timeframe,
                MarketCandle.is_closed.is_(True),
            )
        )
        responses.append(
            MarketStreamResponse(
                exchange=checkpoint.exchange,
                symbol=checkpoint.symbol,
                timeframe=checkpoint.timeframe,
                status=checkpoint.status,
                row_count=int(candle_count or 0),
                last_closed_open_time=checkpoint.last_closed_open_time,
                last_received_at=checkpoint.last_received_at,
                last_persisted_at=checkpoint.last_persisted_at,
                last_backfill_at=checkpoint.last_backfill_at,
                reconnect_count=checkpoint.reconnect_count,
                backfilled_candles=checkpoint.backfilled_candles,
                last_error=checkpoint.last_error,
            )
        )
    return responses
