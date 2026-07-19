from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from apps.api.app.db.base import Base
from apps.api.app.models import MarketCandle
from apps.collector.quant_web3_collector.domain import Candle
from apps.collector.quant_web3_collector.store import MarketDataStore


def make_store():
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    return MarketDataStore(factory), factory


def make_candle(open_time: datetime, close: str = "60050") -> Candle:
    return Candle(
        exchange="binance",
        symbol="BTC/USDT",
        timeframe="1m",
        open_time=open_time,
        close_time=open_time + timedelta(minutes=1),
        open=Decimal("60000"),
        high=Decimal("60100"),
        low=Decimal("59900"),
        close=Decimal(close),
        volume=Decimal("12.5"),
        trade_count=42,
        is_closed=True,
        source="websocket",
        source_event_time=open_time + timedelta(minutes=1),
        received_at=open_time + timedelta(minutes=1, seconds=1),
    )


def test_candle_persistence_is_idempotent() -> None:
    store, factory = make_store()
    open_time = datetime(2026, 7, 19, 12, 0, tzinfo=UTC)

    first = store.persist_candles([make_candle(open_time)])
    second = store.persist_candles([make_candle(open_time, close="60075")])

    assert first.inserted == 1
    assert second.updated == 1
    with factory() as db:
        assert db.scalar(select(func.count(MarketCandle.id))) == 1
        candle = db.scalar(select(MarketCandle))
        assert candle is not None
        assert candle.close == Decimal("60075")


def test_reconciliation_finds_internal_gap() -> None:
    store, _ = make_store()
    first = datetime(2026, 7, 19, 12, 0, tzinfo=UTC)
    store.persist_candles([make_candle(first), make_candle(first + timedelta(minutes=2))])

    start, latest = store.reconciliation_start(
        "binance",
        "BTC/USDT",
        "1m",
        now=datetime(2026, 7, 19, 12, 3, 30, tzinfo=UTC),
        initial_lookback_candles=3,
        gap_lookback_candles=3,
    )

    assert latest == first + timedelta(minutes=2)
    assert start == first + timedelta(minutes=1)
