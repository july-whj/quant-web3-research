"""Protocol implemented by every built-in strategy."""

from __future__ import annotations

from typing import Protocol

import pandas as pd
from pydantic import BaseModel

from .models import StrategySpec


class Strategy(Protocol):
    spec: StrategySpec

    def generate_signals(
        self,
        candles: pd.DataFrame,
        parameters: BaseModel,
    ) -> pd.DataFrame:
        """Return indicators, known-at-close signals, positions, and trades."""

        ...
