"""Read one EVM transaction through a JSON-RPC endpoint."""

from __future__ import annotations

import argparse
import json
import os

from dotenv import load_dotenv

from quant_web3.chain import rpc_call


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("transaction_hash", help="0x-prefixed EVM transaction hash")
    parser.add_argument("--rpc-url", help="overrides WEB3_RPC_URL")
    return parser.parse_args()


def main() -> None:
    load_dotenv()
    args = parse_args()
    rpc_url = args.rpc_url or os.getenv("WEB3_RPC_URL")
    if not rpc_url:
        raise SystemExit("Set WEB3_RPC_URL or pass --rpc-url. Never provide a private key.")

    transaction = rpc_call(rpc_url, "eth_getTransactionByHash", [args.transaction_hash])
    print(json.dumps(transaction, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
