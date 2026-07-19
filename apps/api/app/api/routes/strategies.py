from fastapi import APIRouter

from ...schemas.research import StrategyDefinition, StrategyParameter


router = APIRouter(prefix="/strategies", tags=["strategies"])


@router.get("", response_model=list[StrategyDefinition])
def list_strategies() -> list[StrategyDefinition]:
    return [
        StrategyDefinition(
            name="ma_cross_long_only",
            title="现货多头双均线",
            description="短期均线上穿长期均线后持有现货，下穿后退出。",
            parameters=[
                StrategyParameter(
                    name="fast_window", label="短期均线", type="integer", default=20, minimum=2
                ),
                StrategyParameter(
                    name="slow_window", label="长期均线", type="integer", default=60, minimum=3
                ),
                StrategyParameter(
                    name="fee_rate", label="单次手续费率", type="number", default=0.001, minimum=0
                ),
                StrategyParameter(
                    name="slippage_rate", label="单次滑点率", type="number", default=0.0005, minimum=0
                ),
            ],
        )
    ]
