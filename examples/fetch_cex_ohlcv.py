"""Fetch public exchange candles through CCXT."""

from __future__ import annotations

import argparse

from quant_web3.data import fetch_ohlcv


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exchange", default="binance")
    parser.add_argument("--symbol", default="BTC/USDT")
    parser.add_argument("--timeframe", default="1d")
    parser.add_argument("--limit", type=int, default=100)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    frame = fetch_ohlcv(args.exchange, args.symbol, args.timeframe, args.limit)
    print(frame.tail(10).to_string())


if __name__ == "__main__":
    main()
