"""Spot long-only moving-average crossover strategy."""

from __future__ import annotations

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, model_validator

from quant_web3.indicators import moving_average

from ..models import MarketDataRequirements, StrategyPlot, StrategySpec


class MaCrossParameters(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fast_window: int = Field(
        default=20,
        ge=2,
        le=200,
        title="短期均线",
        description="用于捕捉较短周期价格变化的简单移动平均窗口。",
        json_schema_extra={"x-ui": {"group": "rules", "unit": "根 K 线", "control": "number"}},
    )
    slow_window: int = Field(
        default=60,
        ge=3,
        le=500,
        title="长期均线",
        description="用于判断较长期趋势方向的简单移动平均窗口。",
        json_schema_extra={"x-ui": {"group": "rules", "unit": "根 K 线", "control": "number"}},
    )

    @model_validator(mode="after")
    def validate_windows(self) -> MaCrossParameters:
        if self.fast_window >= self.slow_window:
            raise ValueError("fast_window must be smaller than slow_window")
        return self


def generate_ma_cross_signals(
    close: pd.Series,
    fast_window: int = 20,
    slow_window: int = 60,
) -> pd.DataFrame:
    """Build a close-confirmed signal and next-period long-only position."""

    parameters = MaCrossParameters(fast_window=fast_window, slow_window=slow_window)
    if close.empty:
        raise ValueError("close must not be empty")

    frame = pd.DataFrame({"close": close.astype(float)}).sort_index()
    frame["fast_ma"] = moving_average(frame["close"], parameters.fast_window)
    frame["slow_ma"] = moving_average(frame["close"], parameters.slow_window)
    ready = frame[["fast_ma", "slow_ma"]].notna().all(axis=1)
    frame["signal"] = ((frame["fast_ma"] > frame["slow_ma"]) & ready).astype(float)
    # A signal is only known after the current candle closes. The shifted
    # position therefore becomes effective at the next candle open.
    frame["position"] = frame["signal"].shift(1).fillna(0.0)
    frame["trade"] = frame["position"].diff().fillna(frame["position"])
    return frame


class MaCrossStrategy:
    spec = StrategySpec(
        key="ma_cross_long_only",
        version="1.0.0",
        title="现货多头双均线",
        description="短期均线上穿长期均线后持有现货，下穿后退出。",
        kind="signal",
        parameters_model=MaCrossParameters,
        data_requirements=MarketDataRequirements(fields=("close",)),
        warmup_bars=lambda parameters: parameters.slow_window,
        plots=(
            StrategyPlot(key="fast_ma", label="短期均线", pane="price", color="#4c6fff"),
            StrategyPlot(key="slow_ma", label="长期均线", pane="price", color="#ed9b3b"),
        ),
        explain=lambda parameters: (
            f"MA{parameters.fast_window} 上穿 MA{parameters.slow_window} 后，"
            "在下一根 K 线开盘进入现货多头；下穿后在下一根 K 线开盘退出。"
        ),
    )

    def generate_signals(
        self,
        candles: pd.DataFrame,
        parameters: BaseModel,
    ) -> pd.DataFrame:
        validated = self.spec.validate_parameters(parameters)
        if "close" not in candles:
            raise ValueError("candles must contain close")
        return generate_ma_cross_signals(
            candles["close"],
            fast_window=validated.fast_window,
            slow_window=validated.slow_window,
        )
