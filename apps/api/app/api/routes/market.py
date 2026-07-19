from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Literal

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ...db.session import get_db
from ...models import IngestionCheckpoint, MarketCandle, User, UserSession, UserWallet
from ...schemas.research import (
    MarketCandleItem,
    MarketCandlePageResponse,
    MarketSignalItem,
    MarketSignalPageResponse,
    MarketStreamResponse,
)
from ..dependencies import get_current_identity
from quant_web3.strategies.ma_cross import generate_ma_cross_signals


router = APIRouter(prefix="/market", tags=["market data"])

ExchangeName = Literal["binance", "okx"]
MarketSymbol = Literal["BTC/USDT"]
MarketTimeframe = Literal["1m", "5m", "15m", "1h", "4h", "1d", "1w"]


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _query_closed_candles(
    db: Session,
    *,
    exchange: str,
    symbol: str,
    timeframe: str,
    before: datetime | None,
    fetch_limit: int,
) -> list[MarketCandle]:
    statement = select(MarketCandle).where(
        MarketCandle.exchange == exchange,
        MarketCandle.symbol == symbol,
        MarketCandle.timeframe == timeframe,
        MarketCandle.is_closed.is_(True),
    )
    if before is not None:
        statement = statement.where(MarketCandle.open_time < _as_utc(before))
    statement = statement.order_by(MarketCandle.open_time.desc()).limit(fetch_limit)
    return list(reversed(db.scalars(statement).all()))


def _candle_item(candle: MarketCandle) -> MarketCandleItem:
    return MarketCandleItem(
        open_time=_as_utc(candle.open_time),
        close_time=_as_utc(candle.close_time),
        open=candle.open,
        high=candle.high,
        low=candle.low,
        close=candle.close,
        volume=candle.volume,
        trade_count=candle.trade_count,
        source=candle.source,
    )


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


@router.get("/candles", response_model=MarketCandlePageResponse)
def list_market_candles(
    exchange: ExchangeName,
    symbol: MarketSymbol = "BTC/USDT",
    timeframe: MarketTimeframe = "1h",
    limit: int = Query(default=500, ge=50, le=2000),
    before: datetime | None = None,
    db: Session = Depends(get_db),
    _: tuple[User, UserWallet, UserSession] = Depends(get_current_identity),
) -> MarketCandlePageResponse:
    candles = _query_closed_candles(
        db,
        exchange=exchange,
        symbol=symbol,
        timeframe=timeframe,
        before=before,
        fetch_limit=limit + 1,
    )
    has_more = len(candles) > limit
    visible = candles[-limit:]
    return MarketCandlePageResponse(
        exchange=exchange,
        symbol=symbol,
        timeframe=timeframe,
        items=[_candle_item(candle) for candle in visible],
        next_before=_as_utc(visible[0].open_time) if has_more and visible else None,
        has_more=has_more,
    )


@router.get("/signals", response_model=MarketSignalPageResponse)
def list_market_signals(
    exchange: ExchangeName,
    symbol: MarketSymbol = "BTC/USDT",
    timeframe: MarketTimeframe = "1h",
    limit: int = Query(default=500, ge=50, le=2000),
    before: datetime | None = None,
    fast_window: int = Query(default=20, ge=2, le=499),
    slow_window: int = Query(default=60, ge=3, le=500),
    db: Session = Depends(get_db),
    _: tuple[User, UserWallet, UserSession] = Depends(get_current_identity),
) -> MarketSignalPageResponse:
    if fast_window >= slow_window:
        raise HTTPException(status_code=422, detail="fast_window must be smaller than slow_window")

    candles = _query_closed_candles(
        db,
        exchange=exchange,
        symbol=symbol,
        timeframe=timeframe,
        before=before,
        fetch_limit=limit + slow_window + 2,
    )
    visible = candles[-limit:]
    visible_open_times = {_as_utc(candle.open_time) for candle in visible}
    signals: list[MarketSignalItem] = []

    if candles:
        close = pd.Series(
            [float(candle.close) for candle in candles],
            index=pd.DatetimeIndex([_as_utc(candle.open_time) for candle in candles]),
            dtype="float64",
        )
        signal_frame = generate_ma_cross_signals(
            close,
            fast_window=fast_window,
            slow_window=slow_window,
        )
        for index in range(1, len(candles)):
            trade = signal_frame["trade"].iloc[index]
            if pd.isna(trade) or float(trade) == 0:
                continue
            execution_candle = candles[index]
            execution_time = _as_utc(execution_candle.open_time)
            if execution_time not in visible_open_times:
                continue
            signal_candle = candles[index - 1]
            side: Literal["buy", "sell"] = "buy" if float(trade) > 0 else "sell"
            signals.append(
                MarketSignalItem(
                    signal_time=_as_utc(signal_candle.open_time),
                    execution_time=execution_time,
                    side=side,
                    signal_price=signal_candle.close,
                    execution_price=execution_candle.open,
                    fast_ma=Decimal(str(signal_frame["fast_ma"].iloc[index - 1])),
                    slow_ma=Decimal(str(signal_frame["slow_ma"].iloc[index - 1])),
                    reason="ma_cross_up" if side == "buy" else "ma_cross_down",
                )
            )

    return MarketSignalPageResponse(
        exchange=exchange,
        symbol=symbol,
        timeframe=timeframe,
        fast_window=fast_window,
        slow_window=slow_window,
        items=signals,
    )
