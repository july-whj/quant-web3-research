from __future__ import annotations

import asyncio
import logging
import random

from apps.api.app.core.config import Settings, get_settings

from .backfill import RestBackfiller
from .domain import Candle
from .exchanges import BinanceStream, OkxStream
from .store import MarketDataStore
from .timeframes import timeframe_seconds


logger = logging.getLogger(__name__)


class MarketCollectorService:
    def __init__(
        self,
        settings: Settings | None = None,
        store: MarketDataStore | None = None,
    ):
        self.settings = settings or get_settings()
        self.store = store or MarketDataStore()
        self.backfiller = RestBackfiller(self.settings, self.store)
        self.exchanges = self.settings.collector_exchange_list
        self.symbol = self.settings.collector_symbol
        self.timeframes = self.settings.collector_timeframe_list
        self._validate_configuration()

    def _validate_configuration(self) -> None:
        unsupported_exchanges = set(self.exchanges) - {"binance", "okx"}
        if unsupported_exchanges:
            raise ValueError(f"unsupported collector exchanges: {sorted(unsupported_exchanges)}")
        if not self.exchanges:
            raise ValueError("COLLECTOR_EXCHANGES cannot be empty")
        if self.symbol != "BTC/USDT":
            raise ValueError("the first collector release supports BTC/USDT only")
        if not self.timeframes:
            raise ValueError("COLLECTOR_TIMEFRAMES cannot be empty")
        for timeframe in self.timeframes:
            timeframe_seconds(timeframe)

    async def handle_candle(self, candle: Candle) -> None:
        await asyncio.to_thread(self.store.persist_candles, [candle])

    def _stream(self, exchange: str):
        if exchange == "binance":
            return BinanceStream(
                self.settings.binance_ws_url,
                self.symbol,
                self.timeframes,
            )
        if exchange == "okx":
            return OkxStream(
                self.settings.okx_ws_url,
                self.symbol,
                self.timeframes,
            )
        raise ValueError(f"unsupported exchange: {exchange}")

    async def _mark_connected(self, exchange: str) -> None:
        await asyncio.to_thread(
            self.store.set_status,
            exchange,
            self.symbol,
            self.timeframes,
            "live",
        )

    async def _reconcile_exchange(self, exchange: str) -> None:
        for timeframe in self.timeframes:
            try:
                await self.backfiller.reconcile(exchange, self.symbol, timeframe)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.exception("Backfill failed for %s %s %s", exchange, self.symbol, timeframe)
                await asyncio.to_thread(
                    self.store.set_status,
                    exchange,
                    self.symbol,
                    [timeframe],
                    "degraded",
                    error=str(exc),
                )

    async def reconcile_all(self) -> None:
        await asyncio.gather(*(self._reconcile_exchange(exchange) for exchange in self.exchanges))

    async def _reconcile_loop(self) -> None:
        while True:
            await self.reconcile_all()
            await asyncio.sleep(self.settings.collector_reconcile_interval_seconds)

    async def _stream_forever(self, exchange: str) -> None:
        delay = 1.0
        while True:
            await asyncio.to_thread(
                self.store.set_status,
                exchange,
                self.symbol,
                self.timeframes,
                "connecting",
            )
            try:
                stream = self._stream(exchange)
                await stream.run(
                    self.handle_candle,
                    on_connected=lambda: self._mark_connected(exchange),
                )
                delay = 1.0
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.exception("%s WebSocket disconnected", exchange)
                await asyncio.to_thread(
                    self.store.set_status,
                    exchange,
                    self.symbol,
                    self.timeframes,
                    "disconnected",
                    error=str(exc),
                    increment_reconnect=True,
                )
                await self._reconcile_exchange(exchange)
                await asyncio.sleep(delay + random.uniform(0, min(delay, 3.0)))
                delay = min(delay * 2, self.settings.collector_reconnect_max_delay_seconds)

    async def run_once(self) -> None:
        self.store.ensure_streams(self.exchanges, self.symbol, self.timeframes)
        try:
            await self.reconcile_all()
        finally:
            await self.backfiller.close()

    async def run(self) -> None:
        self.store.ensure_streams(self.exchanges, self.symbol, self.timeframes)
        tasks = [asyncio.create_task(self._stream_forever(exchange)) for exchange in self.exchanges]
        tasks.append(asyncio.create_task(self._reconcile_loop()))
        try:
            await asyncio.gather(*tasks)
        finally:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            await self.backfiller.close()
