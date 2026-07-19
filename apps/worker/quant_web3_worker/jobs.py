from __future__ import annotations

from datetime import UTC, datetime

import numpy as np
import pandas as pd

from apps.api.app.core.config import get_settings
from apps.api.app.db.session import SessionLocal
from apps.api.app.models import BacktestRun
from quant_web3.backtest import run_long_only_backtest
from quant_web3.reporting import summarize_backtest
from quant_web3.strategies import generate_ma_cross_signals


def deterministic_close_series(days: int) -> pd.Series:
    """Build repeatable demo candles until an exchange dataset is selected."""
    dates = pd.date_range(end=pd.Timestamp.now(tz="UTC").normalize(), periods=days, freq="D")
    x = np.arange(days, dtype=float)
    trend = 50_000 + x * 52
    cycle = 4_800 * np.sin(x / 18.0) + 1_900 * np.sin(x / 5.4)
    close = np.maximum(trend + cycle, 1.0)
    return pd.Series(close, index=dates, name="close")


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
            close = deterministic_close_series(run.days)
            signals = generate_ma_cross_signals(
                close,
                fast_window=int(run.parameters["fast_window"]),
                slow_window=int(run.parameters["slow_window"]),
            )
            result = run_long_only_backtest(
                close,
                signals["position"],
                fee_rate=float(run.parameters["fee_rate"]),
                slippage_rate=float(run.parameters["slippage_rate"]),
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
