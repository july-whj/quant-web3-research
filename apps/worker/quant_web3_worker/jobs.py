from __future__ import annotations

from datetime import UTC, datetime

import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.app.core.config import get_settings
from apps.api.app.db.session import SessionLocal
from apps.api.app.models import BacktestRun, MarketCandle
from apps.api.app.services.market_data import as_utc, require_closed_candle_coverage
from quant_web3.backtest import run_long_only_backtest
from quant_web3.reporting import summarize_backtest
from quant_web3.strategies import strategy_registry


def load_market_candles(db: Session, run: BacktestRun) -> tuple[pd.DataFrame, dict[str, object]]:
    stream_filters = (
        MarketCandle.exchange == run.exchange,
        MarketCandle.symbol == run.symbol,
        MarketCandle.timeframe == run.timeframe,
        MarketCandle.is_closed.is_(True),
    )
    strategy = strategy_registry.get(run.strategy_name, run.strategy_version)
    parameters = strategy.spec.validate_parameters(run.parameters)
    minimum_bars = strategy.spec.required_warmup_bars(parameters) + 2
    coverage = require_closed_candle_coverage(
        db,
        exchange=run.exchange,
        symbol=run.symbol,
        timeframe=run.timeframe,
        days=run.days,
        minimum_bars=minimum_bars,
    )
    rows = list(
        db.scalars(
            select(MarketCandle)
            .where(*stream_filters, MarketCandle.open_time >= coverage.requested_start)
            .order_by(MarketCandle.open_time.asc())
        ).all()
    )

    index = pd.DatetimeIndex([as_utc(row.open_time) for row in rows], name="timestamp")
    candles = pd.DataFrame(
        {
            "open": [float(row.open) for row in rows],
            "high": [float(row.high) for row in rows],
            "low": [float(row.low) for row in rows],
            "close": [float(row.close) for row in rows],
            "volume": [float(row.volume) for row in rows],
        },
        index=index,
    )
    snapshot: dict[str, object] = {
        "exchange": run.exchange,
        "symbol": run.symbol,
        "timeframe": run.timeframe,
        "requested_days": run.days,
        "requested_start_time": coverage.requested_start.isoformat(),
        "start_time": coverage.first_open_time.isoformat(),
        "end_time": as_utc(rows[-1].open_time).isoformat(),
        "candle_count": len(rows),
        "expected_candle_count": coverage.expected_candle_count,
        "gap_count": coverage.expected_candle_count - len(rows),
        "closed_candles_only": True,
    }
    return candles, snapshot


def run_backtest_job(run_id: str) -> None:
    settings = get_settings()
    with SessionLocal() as db:
        run = db.get(BacktestRun, run_id)
        if run is None:
            raise ValueError(f"backtest run not found: {run_id}")
        run.status = "running"
        run.started_at = datetime.now(UTC)
        db.commit()

        try:
            strategy = strategy_registry.get(run.strategy_name, run.strategy_version)
            parameters = strategy.spec.validate_parameters(run.parameters)
            candles, data_snapshot = load_market_candles(db, run)
            signals = strategy.generate_signals(candles, parameters)
            execution = run.execution_config or {}
            risk = run.risk_config or {}
            max_position_pct = float(risk.get("max_position_pct", 1.0))
            position = signals["position"] * max_position_pct
            result = run_long_only_backtest(
                candles["close"],
                position,
                open_prices=candles["open"],
                initial_capital=float(execution.get("initial_capital", 1000.0)),
                fee_rate=float(execution.get("fee_rate", 0.001)),
                slippage_rate=float(execution.get("slippage_rate", 0.0005)),
            )
            summary = summarize_backtest(result)
            summary["strategy_total_return"] = float(summary["strategy_return"])
            summary["benchmark_total_return"] = float(summary["benchmark_return"])
            summary = {
                key: int(value) if isinstance(value, (np.integer,)) else float(value)
                if isinstance(value, (np.floating,))
                else value
                for key, value in summary.items()
            }

            artifact_dir = settings.artifact_dir / run.id
            artifact_dir.mkdir(parents=True, exist_ok=True)
            artifact_path = artifact_dir / "equity.parquet"
            result.to_parquet(artifact_path)

            run.summary = summary
            run.data_snapshot = data_snapshot
            run.artifact_path = str(artifact_path.relative_to(settings.artifact_dir.parent.parent))
            run.status = "succeeded"
            run.finished_at = datetime.now(UTC)
            run.error_message = None
            db.commit()
        except Exception as exc:
            run.status = "failed"
            run.error_message = str(exc)[:2000]
            run.finished_at = datetime.now(UTC)
            db.commit()
            raise
