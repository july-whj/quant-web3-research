from __future__ import annotations

from fastapi import HTTPException, status
from redis import Redis
from rq import Queue
from sqlalchemy.orm import Session

from quant_web3.strategies import strategy_registry

from ..core.config import Settings
from ..models import BacktestRun
from ..schemas.research import BacktestCreate
from .market_data import MarketDataCoverageError, require_closed_candle_coverage


def create_and_dispatch_backtest(
    db: Session,
    *,
    owner_id: str,
    payload: BacktestCreate,
    settings: Settings,
    strategy_config_version_id: str | None = None,
) -> BacktestRun:
    """Persist and dispatch one backtest through the same execution path."""

    if settings.job_mode not in {"inline", "rq"}:
        raise HTTPException(status_code=500, detail="JOB_MODE 必须是 inline 或 rq")

    strategy = strategy_registry.get(payload.strategy_name, payload.strategy_version)
    minimum_bars = strategy.spec.required_warmup_bars(payload.parameters) + 2
    try:
        require_closed_candle_coverage(
            db,
            exchange=payload.exchange,
            symbol=payload.symbol,
            timeframe=payload.timeframe,
            days=payload.days,
            minimum_bars=minimum_bars,
        )
    except MarketDataCoverageError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    run = BacktestRun(
        owner_id=owner_id,
        strategy_name=payload.strategy_name,
        strategy_version=payload.strategy_version,
        strategy_config_version_id=strategy_config_version_id,
        exchange=payload.exchange,
        symbol=payload.symbol,
        timeframe=payload.timeframe,
        days=payload.days,
        parameters=payload.parameters,
        risk_config=payload.risk.model_dump(mode="json"),
        execution_config=payload.execution.model_dump(mode="json"),
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    if settings.job_mode == "inline":
        from apps.worker.quant_web3_worker.jobs import run_backtest_job

        run_backtest_job(run.id)
        db.refresh(run)
    else:
        queue = Queue("backtests", connection=Redis.from_url(settings.redis_url))
        queue.enqueue(
            "apps.worker.quant_web3_worker.jobs.run_backtest_job",
            run.id,
            job_id=f"backtest-{run.id}",
            job_timeout=900,
        )
    return run
