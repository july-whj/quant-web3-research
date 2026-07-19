from datetime import UTC, datetime
from decimal import Decimal

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from quant_web3.strategies import StrategyNotFoundError, strategy_registry

from ...db.session import get_db
from ...models import MarketCandle, User, UserSession, UserWallet
from ...schemas.research import (
    MarketCandleItem,
    StrategyDataRequirements,
    StrategyDefinition,
    StrategyPlotDefinition,
    StrategyPreviewPlot,
    StrategyPreviewPoint,
    StrategyPreviewRequest,
    StrategyPreviewResponse,
    StrategyPreviewSignal,
)
from ..dependencies import get_current_identity


router = APIRouter(prefix="/strategies", tags=["strategies"])


@router.get("", response_model=list[StrategyDefinition])
def list_strategies() -> list[StrategyDefinition]:
    definitions: list[StrategyDefinition] = []
    for strategy in strategy_registry.list():
        spec = strategy.spec
        requirements = spec.data_requirements
        definitions.append(
            StrategyDefinition(
                key=spec.key,
                version=spec.version,
                kind=spec.kind,
                title=spec.title,
                description=spec.description,
                default_warmup_bars=spec.default_warmup_bars(),
                data_requirements=StrategyDataRequirements(
                    fields=list(requirements.fields),
                    market_types=list(requirements.market_types),
                    timeframes=list(requirements.timeframes),
                    closed_candles_only=requirements.closed_candles_only,
                ),
                parameters_schema=spec.parameter_schema(),
                plots=[
                    StrategyPlotDefinition(
                        key=plot.key,
                        label=plot.label,
                        pane=plot.pane,
                        color=plot.color,
                    )
                    for plot in spec.plots
                ],
            )
        )
    return definitions


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


@router.post("/{strategy_key}/preview", response_model=StrategyPreviewResponse)
def preview_strategy(
    strategy_key: str,
    payload: StrategyPreviewRequest,
    db: Session = Depends(get_db),
    _: tuple[User, UserWallet, UserSession] = Depends(get_current_identity),
) -> StrategyPreviewResponse:
    try:
        strategy, parameters = strategy_registry.validate_parameters(
            strategy_key,
            payload.parameters,
            payload.strategy_version,
        )
    except (StrategyNotFoundError, ValidationError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    warmup_bars = strategy.spec.required_warmup_bars(parameters)
    rows = list(
        reversed(
            db.scalars(
                select(MarketCandle)
                .where(
                    MarketCandle.exchange == payload.exchange,
                    MarketCandle.symbol == payload.symbol,
                    MarketCandle.timeframe == payload.timeframe,
                    MarketCandle.is_closed.is_(True),
                )
                .order_by(MarketCandle.open_time.desc())
                .limit(payload.limit + warmup_bars + 2)
            ).all()
        )
    )
    if len(rows) < warmup_bars + 2:
        raise HTTPException(
            status_code=422,
            detail=f"策略预览至少需要 {warmup_bars + 2} 根闭合 K 线",
        )

    index = pd.DatetimeIndex([_as_utc(row.open_time) for row in rows])
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
    result = strategy.generate_signals(candles, parameters)
    visible_rows = rows[-payload.limit :]
    visible_times = {_as_utc(row.open_time) for row in visible_rows}

    plots: list[StrategyPreviewPlot] = []
    for plot in strategy.spec.plots:
        if plot.key not in result:
            continue
        points = [
            StrategyPreviewPoint(
                time=_as_utc(time.to_pydatetime()),
                value=Decimal(str(value)),
            )
            for time, value in result[plot.key].items()
            if _as_utc(time.to_pydatetime()) in visible_times and pd.notna(value)
        ]
        plots.append(
            StrategyPreviewPlot(
                key=plot.key,
                label=plot.label,
                pane=plot.pane,
                color=plot.color,
                points=points,
            )
        )

    signals: list[StrategyPreviewSignal] = []
    for position_index in range(1, len(rows)):
        delta = result["trade"].iloc[position_index]
        if pd.isna(delta) or abs(float(delta)) < 1e-12:
            continue
        execution_row = rows[position_index]
        execution_time = _as_utc(execution_row.open_time)
        if execution_time not in visible_times:
            continue
        signal_row = rows[position_index - 1]
        side = "buy" if float(delta) > 0 else "sell"
        signals.append(
            StrategyPreviewSignal(
                signal_time=_as_utc(signal_row.open_time),
                execution_time=execution_time,
                side=side,
                signal_price=signal_row.close,
                execution_price=execution_row.open,
                target_position=Decimal(str(result["position"].iloc[position_index])),
                position_delta=Decimal(str(delta)),
                reason=f"{strategy.spec.key}:{'increase' if side == 'buy' else 'decrease'}",
            )
        )

    return StrategyPreviewResponse(
        strategy_name=strategy.spec.key,
        strategy_version=strategy.spec.version,
        explanation=strategy.spec.explanation(parameters),
        warmup_bars=warmup_bars,
        candles=[
            MarketCandleItem(
                open_time=_as_utc(row.open_time),
                close_time=_as_utc(row.close_time),
                open=row.open,
                high=row.high,
                low=row.low,
                close=row.close,
                volume=row.volume,
                trade_count=row.trade_count,
                source=row.source,
            )
            for row in visible_rows
        ],
        plots=plots,
        signals=signals,
    )
