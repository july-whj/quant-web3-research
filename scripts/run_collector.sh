#!/usr/bin/env bash
set -euo pipefail

python -m apps.collector.quant_web3_collector.main "$@"
