"""Spot long-only RSI mean-reversion strategy."""

from __future__ import annotations

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..models import MarketDataRequirements, StrategyPlot, StrategySpec


class RsiReversalParameters(BaseModel):
    model_config = ConfigDict(extra="forbid")

    period: int = Field(
        default=14,
        ge=2,
        le=100,
        title="RSI 周期",
        description="计算相对强弱指标时使用的 K 线数量。",
        json_schema_extra={"x-ui": {"group": "rules", "unit": "根 K 线"}},
    )
    oversold: float = Field(
        default=30,
        ge=1,
        le=49,
        title="超卖阈值",
        description="RSI 低于该值后产生进入现货多头的信号。",
    )
    overbought: float = Field(
        default=70,
        ge=51,
        le=99,
        title="超买阈值",
        description="RSI 高于该值后产生退出信号。",
    )

    @model_validator(mode="after")
    def validate_thresholds(self) -> RsiReversalParameters:
        if self.oversold >= self.overbought:
            raise ValueError("oversold must be smaller than overbought")
        return self


def relative_strength_index(close: pd.Series, period: int) -> pd.Series:
    delta = close.astype(float).diff()
    gains = delta.clip(lower=0)
    losses = -delta.clip(upper=0)
    average_gain = gains.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    average_loss = losses.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    relative_strength = average_gain / average_loss.replace(0, float("nan"))
    rsi = 100 - 100 / (1 + relative_strength)
    return rsi.where(average_loss != 0, 100.0)


class RsiReversalStrategy:
    spec = StrategySpec(
        key="rsi_reversal_long_only",
        version="1.0.0",
        title="现货多头 RSI 反转",
        description="RSI 进入超卖区后持有现货，进入超买区后退出。",
        kind="signal",
        parameters_model=RsiReversalParameters,
        data_requirements=MarketDataRequirements(fields=("close",)),
        warmup_bars=lambda parameters: parameters.period + 1,
        plots=(
            StrategyPlot(key="rsi", label="RSI", pane="indicator", color="#7132f5"),
            StrategyPlot(key="oversold_line", label="超卖线", pane="indicator", color="#0f9d72"),
            StrategyPlot(key="overbought_line", label="超买线", pane="indicator", color="#e05d5d"),
        ),
        explain=lambda parameters: (
            f"RSI({parameters.period}) 低于 {parameters.oversold:g} 后，下一根 K 线开盘进入；"
            f"高于 {parameters.overbought:g} 后，下一根 K 线开盘退出。"
        ),
    )

    def generate_signals(self, candles: pd.DataFrame, parameters: BaseModel) -> pd.DataFrame:
        validated = self.spec.validate_parameters(parameters)
        if "close" not in candles:
            raise ValueError("candles must contain close")
        frame = pd.DataFrame({"close": candles["close"].astype(float)}).sort_index()
        frame["rsi"] = relative_strength_index(frame["close"], validated.period)
        frame["oversold_line"] = float(validated.oversold)
        frame["overbought_line"] = float(validated.overbought)
        current_position = 0.0
        targets: list[float] = []
        for value in frame["rsi"]:
            if pd.notna(value) and value <= validated.oversold:
                current_position = 1.0
            elif pd.notna(value) and value >= validated.overbought:
                current_position = 0.0
            targets.append(current_position)
        frame["signal"] = targets
        frame["position"] = frame["signal"].shift(1).fillna(0.0)
        frame["trade"] = frame["position"].diff().fillna(frame["position"])
        return frame
