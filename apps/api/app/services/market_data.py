"""Read-only coverage checks for reproducible market-data experiments."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import MarketCandle


TIMEFRAME_SECONDS = {
    "1m": 60,
    "5m": 5 * 60,
    "15m": 15 * 60,
    "1h": 60 * 60,
    "4h": 4 * 60 * 60,
    "1d": 24 * 60 * 60,
    "1w": 7 * 24 * 60 * 60,
}


class MarketDataCoverageError(ValueError):
    pass


def as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


@dataclass(frozen=True)
class MarketDataCoverage:
    requested_start: datetime
    first_open_time: datetime
    latest_open_time: datetime
    candle_count: int
    expected_candle_count: int


def require_closed_candle_coverage(
    db: Session,
    *,
    exchange: str,
    symbol: str,
    timeframe: str,
    days: int,
    minimum_bars: int,
) -> MarketDataCoverage:
    stream_filters = (
        MarketCandle.exchange == exchange,
        MarketCandle.symbol == symbol,
        MarketCandle.timeframe == timeframe,
        MarketCandle.is_closed.is_(True),
    )
    latest_open_time = db.scalar(select(func.max(MarketCandle.open_time)).where(*stream_filters))
    if latest_open_time is None:
        raise MarketDataCoverageError("所选交易所、交易对和周期没有可用于回测的闭合 K 线")

    latest_open_time = as_utc(latest_open_time)
    requested_start = latest_open_time - timedelta(days=days)
    first_open_time, candle_count = db.execute(
        select(func.min(MarketCandle.open_time), func.count(MarketCandle.id)).where(
            *stream_filters,
            MarketCandle.open_time >= requested_start,
        )
    ).one()
    if first_open_time is None or not candle_count:
        raise MarketDataCoverageError("所选回测范围内没有闭合 K 线")

    first_open_time = as_utc(first_open_time)
    step_seconds = TIMEFRAME_SECONDS[timeframe]
    if first_open_time - requested_start > timedelta(seconds=step_seconds):
        raise MarketDataCoverageError(
            "回测数据未覆盖所选时间范围，请先补齐更早行情或缩短回测天数"
        )
    if candle_count < minimum_bars:
        raise MarketDataCoverageError(
            f"回测数据不足：至少需要 {minimum_bars} 根 K 线，当前只有 {candle_count} 根"
        )

    expected_candle_count = (
        int((latest_open_time - first_open_time).total_seconds() // step_seconds) + 1
    )
    if candle_count < expected_candle_count:
        raise MarketDataCoverageError(
            f"回测范围内缺少 {expected_candle_count - candle_count} 根 K 线，请先完成补数"
        )
    return MarketDataCoverage(
        requested_start=requested_start,
        first_open_time=first_open_time,
        latest_open_time=latest_open_time,
        candle_count=int(candle_count),
        expected_candle_count=expected_candle_count,
    )
