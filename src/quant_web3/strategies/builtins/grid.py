"""Adaptive spot grid expressed as a bounded target-position strategy."""

from __future__ import annotations

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

from ..models import MarketDataRequirements, StrategyPlot, StrategySpec


class GridParameters(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lookback_window: int = Field(
        default=60,
        ge=10,
        le=500,
        title="网格中轴周期",
        description="使用滚动均价作为自适应网格中轴。",
        json_schema_extra={"x-ui": {"group": "rules", "unit": "根 K 线"}},
    )
    grid_levels: int = Field(
        default=5,
        ge=2,
        le=20,
        title="单侧网格数量",
        description="中轴上下各自划分的网格层数。",
        json_schema_extra={"x-ui": {"group": "rules", "unit": "层"}},
    )
    grid_spacing_pct: float = Field(
        default=0.02,
        ge=0.001,
        le=0.2,
        title="网格间距",
        description="相邻网格之间相对中轴价格的比例。",
        json_schema_extra={"x-ui": {"group": "rules", "unit": "%", "scale": 100}},
    )


class AdaptiveGridStrategy:
    spec = StrategySpec(
        key="adaptive_spot_grid",
        version="1.0.0",
        title="自适应现货网格",
        description="围绕滚动均价分层调整现货目标仓位，价格越低仓位越高。",
        kind="grid",
        parameters_model=GridParameters,
        data_requirements=MarketDataRequirements(fields=("close",)),
        warmup_bars=lambda parameters: parameters.lookback_window,
        plots=(
            StrategyPlot(key="grid_center", label="网格中轴", pane="price", color="#ed9b3b"),
            StrategyPlot(
                key="target_allocation",
                label="目标仓位",
                pane="indicator",
                color="#7132f5",
            ),
        ),
        explain=lambda parameters: (
            f"以 {parameters.lookback_window} 根 K 线滚动均价为中轴，上下各设 "
            f"{parameters.grid_levels} 层、间距 {parameters.grid_spacing_pct * 100:g}%；"
            "价格低于中轴时逐层增加仓位，高于中轴时逐层减少。"
        ),
    )

    def generate_signals(self, candles: pd.DataFrame, parameters: BaseModel) -> pd.DataFrame:
        validated = self.spec.validate_parameters(parameters)
        if "close" not in candles:
            raise ValueError("candles must contain close")
        frame = pd.DataFrame({"close": candles["close"].astype(float)}).sort_index()
        frame["grid_center"] = frame["close"].rolling(
            validated.lookback_window,
            min_periods=validated.lookback_window,
        ).mean()
        relative_distance = (
            (frame["grid_center"] - frame["close"])
            / frame["grid_center"]
            / validated.grid_spacing_pct
        )
        grid_step = np.floor(relative_distance).clip(
            lower=-validated.grid_levels,
            upper=validated.grid_levels,
        )
        target = (0.5 + grid_step / (2 * validated.grid_levels)).clip(0, 1)
        frame["target_allocation"] = target.where(frame["grid_center"].notna(), 0.0)
        frame["signal"] = frame["target_allocation"]
        frame["position"] = frame["signal"].shift(1).fillna(0.0)
        frame["trade"] = frame["position"].diff().fillna(frame["position"])
        return frame
