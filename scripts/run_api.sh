#!/usr/bin/env bash
set -euo pipefail

uvicorn apps.api.app.main:app --reload --host 127.0.0.1 --port 8000
