from datetime import UTC, datetime

from apps.collector.quant_web3_collector.timeframes import expected_latest_closed_open


def test_latest_closed_minute() -> None:
    now = datetime(2026, 7, 19, 12, 3, 45, tzinfo=UTC)
    assert expected_latest_closed_open(now, "1m") == datetime(
        2026, 7, 19, 12, 2, tzinfo=UTC
    )


def test_latest_closed_week_uses_monday_utc() -> None:
    now = datetime(2026, 7, 19, 12, 0, tzinfo=UTC)  # Sunday
    assert expected_latest_closed_open(now, "1w") == datetime(2026, 7, 6, tzinfo=UTC)
