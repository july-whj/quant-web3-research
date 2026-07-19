from __future__ import annotations

from datetime import UTC, datetime, timedelta


TIMEFRAME_SECONDS = {
    "1s": 1,
    "1m": 60,
    "5m": 5 * 60,
    "15m": 15 * 60,
    "1h": 60 * 60,
    "4h": 4 * 60 * 60,
    "1d": 24 * 60 * 60,
    "1w": 7 * 24 * 60 * 60,
}


def timeframe_seconds(timeframe: str) -> int:
    try:
        return TIMEFRAME_SECONDS[timeframe]
    except KeyError as exc:
        raise ValueError(f"unsupported collector timeframe: {timeframe}") from exc


def timeframe_milliseconds(timeframe: str) -> int:
    return timeframe_seconds(timeframe) * 1000


def expected_latest_closed_open(now: datetime, timeframe: str) -> datetime:
    """Return the opening timestamp of the latest fully closed UTC candle."""
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    current = now.astimezone(UTC)
    if timeframe == "1w":
        current_day = current.replace(hour=0, minute=0, second=0, microsecond=0)
        current_week = current_day - timedelta(days=current_day.weekday())
        return current_week - timedelta(weeks=1)
    duration = timeframe_seconds(timeframe)
    current_bucket = int(current.timestamp()) // duration * duration
    return datetime.fromtimestamp(current_bucket - duration, tz=UTC)


def iter_open_times(start: datetime, end: datetime, timeframe: str):
    step = timedelta(seconds=timeframe_seconds(timeframe))
    current = start
    while current <= end:
        yield current
        current += step
