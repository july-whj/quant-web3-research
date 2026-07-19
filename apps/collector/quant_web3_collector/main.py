from __future__ import annotations

import argparse
import asyncio
import logging

from .service import MarketCollectorService


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect and repair public BTC/USDT candles.")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run one REST reconciliation pass and exit without WebSocket subscriptions.",
    )
    return parser.parse_args()


async def async_main(run_once: bool) -> None:
    service = MarketCollectorService()
    if run_once:
        await service.run_once()
    else:
        await service.run()


def main() -> None:
    args = parse_args()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    try:
        asyncio.run(async_main(args.once))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
