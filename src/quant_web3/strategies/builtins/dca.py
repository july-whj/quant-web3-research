"""A finite staged-allocation strategy for educational DCA experiments."""

from __future__ import annotations

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

from ..models import MarketDataRequirements, StrategyPlot, StrategySpec


class DcaParameters(BaseModel):
    model_config = ConfigDict(extra="forbid")

    interval_bars: int = Field(
        default=7,
        ge=1,
        le=365,
        title="投入间隔",
        description="每隔多少根 K 线增加一次目标仓位。",
        json_schema_extra={"x-ui": {"group": "rules", "unit": "根 K 线"}},
    )
    installments: int = Field(
        default=12,
        ge=2,
        le=100,
        title="分批次数",
        description="将计划资金平均拆分成多少次投入。",
        json_schema_extra={"x-ui": {"group": "rules", "unit": "次"}},
    )


class DcaStrategy:
    spec = StrategySpec(
        key="staged_dca_long_only",
        version="1.0.0",
        title="现货分批定投",
        description="按固定 K 线间隔逐步增加仓位，直至完成计划投入。",
        kind="schedule",
        parameters_model=DcaParameters,
        data_requirements=MarketDataRequirements(fields=("close",)),
        warmup_bars=lambda _parameters: 1,
        plots=(
            StrategyPlot(
                key="target_allocation",
                label="目标仓位",
                pane="indicator",
                color="#4c6fff",
            ),
        ),
        explain=lambda parameters: (
            f"把计划资金拆成 {parameters.installments} 份，每隔 {parameters.interval_bars} 根 K 线"
            "增加一份目标仓位，并在下一根 K 线开盘执行。"
        ),
    )

    def generate_signals(self, candles: pd.DataFrame, parameters: BaseModel) -> pd.DataFrame:
        validated = self.spec.validate_parameters(parameters)
        if "close" not in candles:
            raise ValueError("candles must contain close")
        frame = pd.DataFrame({"close": candles["close"].astype(float)}).sort_index()
        steps = np.floor(np.arange(len(frame)) / validated.interval_bars) + 1
        target = np.minimum(steps / validated.installments, 1.0)
        frame["target_allocation"] = target
        frame["signal"] = target
        frame["position"] = frame["signal"].shift(1).fillna(0.0)
        frame["trade"] = frame["position"].diff().fillna(frame["position"])
        return frame
