from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from decimal import Decimal

import ccxt.async_support as ccxt_async

from apps.api.app.core.config import Settings

from .domain import Candle, datetime_from_milliseconds, utc_now
from .store import MarketDataStore
from .timeframes import timeframe_milliseconds


logger = logging.getLogger(__name__)


def okx_rest_params(timeframe: str) -> dict[str, str]:
    if timeframe == "1d":
        return {"bar": "1Dutc"}
    if timeframe == "1w":
        return {"bar": "1Wutc"}
    return {}


class RestBackfiller:
    def __init__(self, settings: Settings, store: MarketDataStore):
        self.settings = settings
        self.store = store
        self.exchanges: dict[str, object] = {}

    async def _exchange(self, exchange_id: str):
        exchange = self.exchanges.get(exchange_id)
        if exchange is not None:
            return exchange
        exchange_class = getattr(ccxt_async, exchange_id, None)
        if exchange_class is None:
            raise ValueError(f"unsupported CCXT exchange: {exchange_id}")
        exchange_config: dict = {"enableRateLimit": True}
        if exchange_id == "binance":
            exchange_config["options"] = {
                "defaultType": "spot",
                "fetchMarkets": {"types": ["spot"]},
            }
        exchange = exchange_class(exchange_config)
        if exchange_id == "binance":
            # Binance exposes a data-only Spot REST endpoint that is a better fit
            # for this public, credential-free collector.
            exchange.urls["api"]["public"] = self.settings.binance_rest_url
        try:
            await exchange.load_markets()
        except BaseException:
            await exchange.close()
            raise
        if not exchange.has.get("fetchOHLCV"):
            await exchange.close()
            raise ValueError(f"{exchange_id} does not support fetchOHLCV")
        self.exchanges[exchange_id] = exchange
        return exchange

    async def reconcile(
        self,
        exchange_id: str,
        symbol: str,
        timeframe: str,
        *,
        now: datetime | None = None,
    ) -> int:
        current_time = now or utc_now()
        start, latest_expected = await asyncio.to_thread(
            self.store.reconciliation_start,
            exchange_id,
            symbol,
            timeframe,
            now=current_time,
            initial_lookback_candles=self.settings.collector_initial_lookback_candles,
            gap_lookback_candles=self.settings.collector_gap_lookback_candles,
        )
        if start is None or start > latest_expected:
            await asyncio.to_thread(
                self.store.mark_backfill_checked,
                exchange_id,
                symbol,
                timeframe,
            )
            return 0

        exchange = await self._exchange(exchange_id)
        supported_timeframes = exchange.timeframes or {}
        if timeframe not in supported_timeframes:
            raise ValueError(f"{exchange_id} does not support {timeframe} OHLCV")

        timeframe_ms = timeframe_milliseconds(timeframe)
        since_ms = int(start.timestamp() * 1000)
        latest_expected_ms = int(latest_expected.timestamp() * 1000)
        total_inserted = 0
        params = okx_rest_params(timeframe) if exchange_id == "okx" else {}
        for _ in range(self.settings.collector_backfill_max_pages):
            rows = await exchange.fetch_ohlcv(
                symbol,
                timeframe=timeframe,
                since=since_ms,
                limit=self.settings.collector_backfill_page_size,
                params=params,
            )
            if not rows:
                break
            received_at = utc_now()
            candles: list[Candle] = []
            last_open_ms = since_ms - timeframe_ms
            for row in rows:
                open_ms = int(row[0])
                last_open_ms = max(last_open_ms, open_ms)
                if open_ms < since_ms or open_ms > latest_expected_ms:
                    continue
                candle = Candle(
                    exchange=exchange_id,
                    symbol=symbol,
                    timeframe=timeframe,
                    open_time=datetime_from_milliseconds(open_ms),
                    close_time=datetime_from_milliseconds(open_ms + timeframe_ms),
                    open=Decimal(str(row[1])),
                    high=Decimal(str(row[2])),
                    low=Decimal(str(row[3])),
                    close=Decimal(str(row[4])),
                    volume=Decimal(str(row[5])),
                    trade_count=None,
                    is_closed=True,
                    source="rest",
                    source_event_time=None,
                    received_at=received_at,
                )
                candle.validate()
                candles.append(candle)
            if candles:
                result = await asyncio.to_thread(self.store.persist_candles, candles)
                total_inserted += result.inserted
            if last_open_ms < since_ms or last_open_ms >= latest_expected_ms:
                break
            since_ms = last_open_ms + timeframe_ms

        await asyncio.to_thread(
            self.store.mark_backfill_checked,
            exchange_id,
            symbol,
            timeframe,
        )
        logger.info(
            "Backfill checked %s %s %s through %s (%s new candles)",
            exchange_id,
            symbol,
            timeframe,
            latest_expected.isoformat(),
            total_inserted,
        )
        return total_inserted

    async def close(self) -> None:
        exchanges = list(self.exchanges.values())
        self.exchanges.clear()
        await asyncio.gather(*(exchange.close() for exchange in exchanges), return_exceptions=True)
