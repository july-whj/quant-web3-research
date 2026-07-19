from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class Candle:
    exchange: str
    symbol: str
    timeframe: str
    open_time: datetime
    close_time: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    is_closed: bool
    source: str
    received_at: datetime
    source_event_time: datetime | None = None
    trade_count: int | None = None

    def as_source(self, source: str) -> Candle:
        return replace(self, source=source)

    def validate(self) -> None:
        if self.open_time.tzinfo is None or self.close_time.tzinfo is None:
            raise ValueError("candle timestamps must be timezone-aware")
        if self.close_time <= self.open_time:
            raise ValueError("candle close_time must be after open_time")
        if self.low > min(self.open, self.close) or self.high < max(self.open, self.close):
            raise ValueError("candle OHLC values are inconsistent")
        if self.high < self.low:
            raise ValueError("candle high must be greater than or equal to low")
        if self.volume < 0:
            raise ValueError("candle volume cannot be negative")


def utc_now() -> datetime:
    return datetime.now(UTC)


def datetime_from_milliseconds(value: int | str) -> datetime:
    return datetime.fromtimestamp(int(value) / 1000, tz=UTC)
