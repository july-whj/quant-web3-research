from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import uuid

from sqlalchemy import func, select
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session, sessionmaker

from apps.api.app.db.session import SessionLocal
from apps.api.app.models import IngestionCheckpoint, MarketCandle

from .domain import Candle, utc_now
from .timeframes import expected_latest_closed_open, iter_open_times, timeframe_seconds


@dataclass(frozen=True, slots=True)
class PersistResult:
    inserted: int = 0
    updated: int = 0


def as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


class MarketDataStore:
    def __init__(self, session_factory: sessionmaker[Session] = SessionLocal):
        self.session_factory = session_factory

    @staticmethod
    def _checkpoint(
        db: Session,
        exchange: str,
        symbol: str,
        timeframe: str,
    ) -> IngestionCheckpoint:
        checkpoint = db.scalar(
            select(IngestionCheckpoint).where(
                IngestionCheckpoint.exchange == exchange,
                IngestionCheckpoint.symbol == symbol,
                IngestionCheckpoint.timeframe == timeframe,
            )
        )
        if checkpoint is None:
            checkpoint = IngestionCheckpoint(
                exchange=exchange,
                symbol=symbol,
                timeframe=timeframe,
                status="starting",
            )
            db.add(checkpoint)
            db.flush()
        return checkpoint

    def ensure_streams(self, exchanges: list[str], symbol: str, timeframes: list[str]) -> None:
        with self.session_factory() as db:
            for exchange in exchanges:
                for timeframe in timeframes:
                    self._checkpoint(db, exchange, symbol, timeframe)
            db.commit()

    def set_status(
        self,
        exchange: str,
        symbol: str,
        timeframes: list[str],
        status: str,
        *,
        error: str | None = None,
        increment_reconnect: bool = False,
    ) -> None:
        with self.session_factory() as db:
            for timeframe in timeframes:
                checkpoint = self._checkpoint(db, exchange, symbol, timeframe)
                checkpoint.status = status
                checkpoint.last_error = error[:2000] if error else None
                if increment_reconnect:
                    checkpoint.reconnect_count += 1
            db.commit()

    def persist_candles(self, candles: list[Candle]) -> PersistResult:
        if not candles:
            return PersistResult()
        inserted = 0
        updated = 0
        persisted_at = utc_now()
        with self.session_factory() as db:
            for candle in sorted(candles, key=lambda item: item.open_time):
                candle.validate()
                existing = db.scalar(
                    select(MarketCandle).where(
                        MarketCandle.exchange == candle.exchange,
                        MarketCandle.symbol == candle.symbol,
                        MarketCandle.timeframe == candle.timeframe,
                        MarketCandle.open_time == candle.open_time,
                    )
                )
                mutable_values = {
                    "close_time": candle.close_time,
                    "open": candle.open,
                    "high": candle.high,
                    "low": candle.low,
                    "close": candle.close,
                    "volume": candle.volume,
                    "trade_count": candle.trade_count,
                    "is_closed": candle.is_closed,
                    "source": candle.source,
                    "source_event_time": candle.source_event_time,
                    "received_at": candle.received_at,
                    "updated_at": persisted_at,
                }
                insert_values = {
                    "id": str(uuid.uuid4()),
                    "exchange": candle.exchange,
                    "symbol": candle.symbol,
                    "timeframe": candle.timeframe,
                    "open_time": candle.open_time,
                    "created_at": persisted_at,
                    **mutable_values,
                }
                dialect = db.get_bind().dialect.name
                if dialect == "mysql":
                    statement = mysql_insert(MarketCandle).values(**insert_values)
                    statement = statement.on_duplicate_key_update(
                        **{
                            name: getattr(statement.inserted, name)
                            for name in mutable_values
                        }
                    )
                    db.execute(statement)
                elif dialect == "sqlite":
                    statement = sqlite_insert(MarketCandle).values(**insert_values)
                    statement = statement.on_conflict_do_update(
                        index_elements=["exchange", "symbol", "timeframe", "open_time"],
                        set_={
                            name: getattr(statement.excluded, name)
                            for name in mutable_values
                        },
                    )
                    db.execute(statement)
                elif existing is None:
                    db.add(MarketCandle(**insert_values))
                else:
                    for name, value in mutable_values.items():
                        setattr(existing, name, value)

                if existing is None:
                    inserted += 1
                else:
                    updated += 1

                checkpoint = self._checkpoint(
                    db,
                    candle.exchange,
                    candle.symbol,
                    candle.timeframe,
                )
                last_closed = as_utc(checkpoint.last_closed_open_time)
                if last_closed is None or candle.open_time > last_closed:
                    checkpoint.last_closed_open_time = candle.open_time
                checkpoint.last_event_time = candle.source_event_time
                checkpoint.last_received_at = candle.received_at
                checkpoint.last_persisted_at = persisted_at
                checkpoint.status = "live" if candle.source == "websocket" else checkpoint.status
                checkpoint.last_error = None
            if candles[0].source == "rest":
                for stream in {(item.exchange, item.symbol, item.timeframe) for item in candles}:
                    checkpoint = self._checkpoint(db, *stream)
                    checkpoint.backfilled_candles += sum(
                        1
                        for item in candles
                        if (item.exchange, item.symbol, item.timeframe) == stream
                    )
                    checkpoint.last_backfill_at = persisted_at
            db.commit()
        return PersistResult(inserted=inserted, updated=updated)

    def mark_backfill_checked(self, exchange: str, symbol: str, timeframe: str) -> None:
        with self.session_factory() as db:
            checkpoint = self._checkpoint(db, exchange, symbol, timeframe)
            checkpoint.last_backfill_at = utc_now()
            checkpoint.last_error = None
            if checkpoint.status in {"starting", "degraded"}:
                checkpoint.status = "ready"
            db.commit()

    def reconciliation_start(
        self,
        exchange: str,
        symbol: str,
        timeframe: str,
        *,
        now: datetime,
        initial_lookback_candles: int,
        gap_lookback_candles: int,
    ) -> tuple[datetime | None, datetime]:
        latest_expected = expected_latest_closed_open(now, timeframe)
        step = timedelta(seconds=timeframe_seconds(timeframe))
        initial_start = latest_expected - step * max(initial_lookback_candles - 1, 0)
        gap_start = latest_expected - step * max(gap_lookback_candles - 1, 0)
        with self.session_factory() as db:
            checkpoint = self._checkpoint(db, exchange, symbol, timeframe)
            db.commit()
            last_closed = as_utc(checkpoint.last_closed_open_time)
            if last_closed is None:
                return initial_start, latest_expected
            if last_closed < gap_start:
                return last_closed + step, latest_expected

            rows = db.scalars(
                select(MarketCandle.open_time).where(
                    MarketCandle.exchange == exchange,
                    MarketCandle.symbol == symbol,
                    MarketCandle.timeframe == timeframe,
                    MarketCandle.open_time >= gap_start,
                    MarketCandle.open_time <= latest_expected,
                    MarketCandle.is_closed.is_(True),
                )
            ).all()
            available = {as_utc(item) for item in rows}
            for expected in iter_open_times(gap_start, latest_expected, timeframe):
                if expected not in available:
                    return expected, latest_expected
        return None, latest_expected

    def stream_statuses(self) -> list[dict]:
        with self.session_factory() as db:
            checkpoints = list(
                db.scalars(
                    select(IngestionCheckpoint).order_by(
                        IngestionCheckpoint.exchange,
                        IngestionCheckpoint.timeframe,
                    )
                ).all()
            )
            statuses: list[dict] = []
            for checkpoint in checkpoints:
                candle_count = db.scalar(
                    select(func.count(MarketCandle.id)).where(
                        MarketCandle.exchange == checkpoint.exchange,
                        MarketCandle.symbol == checkpoint.symbol,
                        MarketCandle.timeframe == checkpoint.timeframe,
                        MarketCandle.is_closed.is_(True),
                    )
                )
                statuses.append(
                    {
                        "exchange": checkpoint.exchange,
                        "symbol": checkpoint.symbol,
                        "timeframe": checkpoint.timeframe,
                        "status": checkpoint.status,
                        "row_count": int(candle_count or 0),
                        "last_closed_open_time": checkpoint.last_closed_open_time,
                        "last_received_at": checkpoint.last_received_at,
                        "last_persisted_at": checkpoint.last_persisted_at,
                        "last_backfill_at": checkpoint.last_backfill_at,
                        "reconnect_count": checkpoint.reconnect_count,
                        "backfilled_candles": checkpoint.backfilled_candles,
                        "last_error": checkpoint.last_error,
                    }
                )
            return statuses
