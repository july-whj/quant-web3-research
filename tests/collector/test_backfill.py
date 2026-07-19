import asyncio
from datetime import UTC, datetime

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from apps.api.app.core.config import Settings
from apps.api.app.db.base import Base
from apps.api.app.models import IngestionCheckpoint, MarketCandle
from apps.collector.quant_web3_collector.backfill import RestBackfiller
from apps.collector.quant_web3_collector.store import MarketDataStore


class FakeExchange:
    has = {"fetchOHLCV": True}
    timeframes = {"1m": "1m"}

    def __init__(self, rows):
        self.rows = rows
        self.fetch_count = 0

    async def fetch_ohlcv(self, symbol, timeframe, since, limit, params):
        self.fetch_count += 1
        return [row for row in self.rows if row[0] >= since][:limit]

    async def close(self):
        return None


def test_rest_backfill_fills_initial_range_and_becomes_idempotent() -> None:
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    store = MarketDataStore(factory)
    settings = Settings(
        _env_file=None,
        collector_initial_lookback_candles=3,
        collector_gap_lookback_candles=3,
        collector_backfill_page_size=300,
        collector_backfill_max_pages=2,
    )
    rows = [
        [1_774_185_600_000, 60_000, 60_100, 59_900, 60_050, 12],
        [1_774_185_660_000, 60_050, 60_150, 60_000, 60_100, 11],
        [1_774_185_720_000, 60_100, 60_200, 60_050, 60_150, 10],
    ]
    exchange = FakeExchange(rows)
    backfiller = RestBackfiller(settings, store)
    backfiller.exchanges["binance"] = exchange
    now = datetime.fromtimestamp((rows[-1][0] + 90_000) / 1000, tz=UTC)

    first = asyncio.run(backfiller.reconcile("binance", "BTC/USDT", "1m", now=now))
    second = asyncio.run(backfiller.reconcile("binance", "BTC/USDT", "1m", now=now))

    assert first == 3
    assert second == 0
    with factory() as db:
        assert db.scalar(select(func.count(MarketCandle.id))) == 3
        checkpoint = db.scalar(select(IngestionCheckpoint))
        assert checkpoint is not None
        assert checkpoint.status == "ready"


def test_rest_backfill_repairs_an_internal_gap() -> None:
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    store = MarketDataStore(factory)
    settings = Settings(
        _env_file=None,
        collector_initial_lookback_candles=3,
        collector_gap_lookback_candles=3,
        collector_backfill_page_size=300,
        collector_backfill_max_pages=2,
    )
    rows = [
        [1_774_185_600_000, 60_000, 60_100, 59_900, 60_050, 12],
        [1_774_185_660_000, 60_050, 60_150, 60_000, 60_100, 11],
        [1_774_185_720_000, 60_100, 60_200, 60_050, 60_150, 10],
    ]
    exchange = FakeExchange(rows)
    backfiller = RestBackfiller(settings, store)
    backfiller.exchanges["binance"] = exchange
    now = datetime.fromtimestamp((rows[-1][0] + 90_000) / 1000, tz=UTC)

    asyncio.run(backfiller.reconcile("binance", "BTC/USDT", "1m", now=now))
    with factory() as db:
        middle = db.scalar(
            select(MarketCandle).where(
                MarketCandle.open_time
                == datetime.fromtimestamp(rows[1][0] / 1000, tz=UTC)
            )
        )
        assert middle is not None
        db.delete(middle)
        db.commit()

    repaired = asyncio.run(backfiller.reconcile("binance", "BTC/USDT", "1m", now=now))

    assert repaired == 1
    with factory() as db:
        assert db.scalar(select(func.count(MarketCandle.id))) == 3
