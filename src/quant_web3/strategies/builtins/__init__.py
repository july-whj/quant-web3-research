"""Built-in strategies shipped with the research system."""

from .dca import DcaParameters, DcaStrategy
from .grid import AdaptiveGridStrategy, GridParameters
from .ma_cross import MaCrossParameters, MaCrossStrategy, generate_ma_cross_signals
from .rsi_reversal import RsiReversalParameters, RsiReversalStrategy

__all__ = [
    "AdaptiveGridStrategy",
    "DcaParameters",
    "DcaStrategy",
    "GridParameters",
    "MaCrossParameters",
    "MaCrossStrategy",
    "RsiReversalParameters",
    "RsiReversalStrategy",
    "generate_ma_cross_signals",
]
