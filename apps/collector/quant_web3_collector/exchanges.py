from __future__ import annotations

import asyncio
import json
import logging
import time
from collections.abc import Awaitable, Callable
from decimal import Decimal
from typing import Any

from websockets.asyncio.client import connect

from .domain import Candle, datetime_from_milliseconds, utc_now
from .timeframes import timeframe_milliseconds


logger = logging.getLogger(__name__)
CandleHandler = Callable[[Candle], Awaitable[None]]
ConnectionHandler = Callable[[], Awaitable[None]]

BINANCE_TIMEFRAMES = {item: item for item in ("1s", "1m", "5m", "15m", "1h", "4h", "1d", "1w")}
OKX_TIMEFRAMES = {
    "1s": "candle1s",
    "1m": "candle1m",
    "5m": "candle5m",
    "15m": "candle15m",
    "1h": "candle1H",
    "4h": "candle4H",
    "1d": "candle1Dutc",
    "1w": "candle1Wutc",
}
OKX_CHANNEL_TIMEFRAMES = {value: key for key, value in OKX_TIMEFRAMES.items()}


def parse_binance_message(
    payload: dict[str, Any],
    *,
    symbol: str = "BTC/USDT",
    received_at=None,
) -> Candle | None:
    data = payload.get("data", payload)
    if data.get("e") != "kline" or "k" not in data:
        return None
    kline = data["k"]
    if not bool(kline.get("x")):
        return None
    candle = Candle(
        exchange="binance",
        symbol=symbol,
        timeframe=str(kline["i"]),
        open_time=datetime_from_milliseconds(kline["t"]),
        close_time=datetime_from_milliseconds(kline["T"] + 1),
        open=Decimal(kline["o"]),
        high=Decimal(kline["h"]),
        low=Decimal(kline["l"]),
        close=Decimal(kline["c"]),
        volume=Decimal(kline["v"]),
        trade_count=int(kline["n"]),
        is_closed=True,
        source="websocket",
        source_event_time=datetime_from_milliseconds(data["E"]),
        received_at=received_at or utc_now(),
    )
    candle.validate()
    return candle


def parse_okx_message(
    payload: dict[str, Any],
    *,
    symbol: str = "BTC/USDT",
    received_at=None,
) -> list[Candle]:
    argument = payload.get("arg") or {}
    timeframe = OKX_CHANNEL_TIMEFRAMES.get(argument.get("channel"))
    if not timeframe:
        return []
    received = received_at or utc_now()
    duration_ms = timeframe_milliseconds(timeframe)
    candles: list[Candle] = []
    for row in payload.get("data") or []:
        if len(row) < 9 or str(row[8]) != "1":
            continue
        open_milliseconds = int(row[0])
        candle = Candle(
            exchange="okx",
            symbol=symbol,
            timeframe=timeframe,
            open_time=datetime_from_milliseconds(open_milliseconds),
            close_time=datetime_from_milliseconds(open_milliseconds + duration_ms),
            open=Decimal(row[1]),
            high=Decimal(row[2]),
            low=Decimal(row[3]),
            close=Decimal(row[4]),
            volume=Decimal(row[5]),
            is_closed=True,
            source="websocket",
            source_event_time=None,
            received_at=received,
        )
        candle.validate()
        candles.append(candle)
    return candles


class BinanceStream:
    def __init__(self, url: str, symbol: str, timeframes: list[str]):
        unsupported = set(timeframes) - BINANCE_TIMEFRAMES.keys()
        if unsupported:
            raise ValueError(f"Binance WebSocket does not support: {sorted(unsupported)}")
        if symbol != "BTC/USDT":
            raise ValueError("the first collector release supports BTC/USDT only")
        self.url = url
        self.symbol = symbol
        self.timeframes = timeframes

    async def run(
        self,
        handler: CandleHandler,
        on_connected: ConnectionHandler | None = None,
    ) -> None:
        streams = [f"btcusdt@kline_{BINANCE_TIMEFRAMES[item]}" for item in self.timeframes]
        async with connect(
            self.url,
            open_timeout=20,
            close_timeout=10,
            ping_interval=None,
            max_size=2**20,
        ) as websocket:
            await websocket.send(json.dumps({"method": "SUBSCRIBE", "params": streams, "id": 1}))
            if on_connected is not None:
                await on_connected()
            started_at = time.monotonic()
            logger.info("Binance WebSocket subscribed to %s", ",".join(streams))
            while time.monotonic() - started_at < 23 * 60 * 60 + 50 * 60:
                raw_message = await asyncio.wait_for(websocket.recv(), timeout=45)
                payload = json.loads(raw_message)
                if payload.get("e") == "serverShutdown":
                    raise ConnectionError("Binance announced a WebSocket server shutdown")
                candle = parse_binance_message(payload, symbol=self.symbol)
                if candle is not None:
                    await handler(candle)
        raise ConnectionError("rotating Binance WebSocket before the 24-hour connection limit")


class OkxStream:
    def __init__(self, url: str, symbol: str, timeframes: list[str]):
        unsupported = set(timeframes) - OKX_TIMEFRAMES.keys()
        if unsupported:
            raise ValueError(f"OKX WebSocket does not support: {sorted(unsupported)}")
        if symbol != "BTC/USDT":
            raise ValueError("the first collector release supports BTC/USDT only")
        self.url = url
        self.symbol = symbol
        self.timeframes = timeframes

    async def run(
        self,
        handler: CandleHandler,
        on_connected: ConnectionHandler | None = None,
    ) -> None:
        arguments = [
            {"channel": OKX_TIMEFRAMES[timeframe], "instId": "BTC-USDT"}
            for timeframe in self.timeframes
        ]
        async with connect(
            self.url,
            open_timeout=20,
            close_timeout=10,
            ping_interval=None,
            max_size=2**20,
        ) as websocket:
            await websocket.send(json.dumps({"op": "subscribe", "args": arguments}))
            if on_connected is not None:
                await on_connected()
            logger.info("OKX WebSocket subscribed to %s", ",".join(item["channel"] for item in arguments))
            while True:
                try:
                    raw_message = await asyncio.wait_for(websocket.recv(), timeout=20)
                except TimeoutError:
                    await websocket.send("ping")
                    raw_message = await asyncio.wait_for(websocket.recv(), timeout=10)
                if raw_message == "pong":
                    continue
                payload = json.loads(raw_message)
                if payload.get("event") == "error":
                    raise ConnectionError(f"OKX subscription error: {payload.get('msg', payload)}")
                for candle in parse_okx_message(payload, symbol=self.symbol):
                    await handler(candle)
