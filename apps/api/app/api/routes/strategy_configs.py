from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...core.config import Settings, get_settings
from ...db.session import get_db
from ...models import StrategyConfig, StrategyConfigVersion, User, UserSession, UserWallet
from ...schemas.research import (
    BacktestCreate,
    BacktestResponse,
    StrategyConfigBacktestCreate,
    StrategyConfigCreate,
    StrategyConfigResponse,
    StrategyConfigVersionCreate,
    StrategyConfigVersionResponse,
)
from ...services.backtests import create_and_dispatch_backtest
from ..dependencies import get_current_identity


router = APIRouter(prefix="/strategy-configs", tags=["strategy-configs"])


def _version_response(version: StrategyConfigVersion) -> StrategyConfigVersionResponse:
    return StrategyConfigVersionResponse.model_validate(version)


def _config_response(
    db: Session,
    config: StrategyConfig,
) -> StrategyConfigResponse:
    versions = list(
        db.scalars(
            select(StrategyConfigVersion)
            .where(StrategyConfigVersion.config_id == config.id)
            .order_by(StrategyConfigVersion.version_number.desc())
        ).all()
    )
    return StrategyConfigResponse(
        id=config.id,
        name=config.name,
        status=config.status,
        latest_version_number=config.latest_version_number,
        created_at=config.created_at,
        updated_at=config.updated_at,
        versions=[_version_response(version) for version in versions],
    )


def _owned_config(db: Session, config_id: str, owner_id: str) -> StrategyConfig:
    config = db.scalar(
        select(StrategyConfig).where(
            StrategyConfig.id == config_id,
            StrategyConfig.owner_id == owner_id,
        )
    )
    if config is None:
        raise HTTPException(status_code=404, detail="策略配置不存在")
    return config


def _make_version(
    config_id: str,
    version_number: int,
    payload: StrategyConfigCreate | StrategyConfigVersionCreate,
) -> StrategyConfigVersion:
    return StrategyConfigVersion(
        config_id=config_id,
        version_number=version_number,
        strategy_name=payload.strategy_name,
        strategy_version=payload.strategy_version,
        exchange=payload.exchange,
        symbol=payload.symbol,
        timeframe=payload.timeframe,
        days=payload.days,
        parameters=payload.parameters,
        risk_config=payload.risk.model_dump(mode="json"),
        execution_config=payload.execution.model_dump(mode="json"),
    )


@router.get("", response_model=list[StrategyConfigResponse])
def list_strategy_configs(
    db: Session = Depends(get_db),
    identity: tuple[User, UserWallet, UserSession] = Depends(get_current_identity),
) -> list[StrategyConfigResponse]:
    user, _, _ = identity
    configs = list(
        db.scalars(
            select(StrategyConfig)
            .where(StrategyConfig.owner_id == user.id)
            .order_by(StrategyConfig.updated_at.desc())
        ).all()
    )
    return [_config_response(db, config) for config in configs]


@router.post("", response_model=StrategyConfigResponse, status_code=status.HTTP_201_CREATED)
def create_strategy_config(
    payload: StrategyConfigCreate,
    db: Session = Depends(get_db),
    identity: tuple[User, UserWallet, UserSession] = Depends(get_current_identity),
) -> StrategyConfigResponse:
    user, _, _ = identity
    config = StrategyConfig(owner_id=user.id, name=payload.name, latest_version_number=1)
    db.add(config)
    db.flush()
    db.add(_make_version(config.id, 1, payload))
    db.commit()
    db.refresh(config)
    return _config_response(db, config)


@router.post(
    "/{config_id}/versions",
    response_model=StrategyConfigResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_strategy_config_version(
    config_id: str,
    payload: StrategyConfigVersionCreate,
    db: Session = Depends(get_db),
    identity: tuple[User, UserWallet, UserSession] = Depends(get_current_identity),
) -> StrategyConfigResponse:
    user, _, _ = identity
    config = db.scalar(
        select(StrategyConfig)
        .where(StrategyConfig.id == config_id, StrategyConfig.owner_id == user.id)
        .with_for_update()
    )
    if config is None:
        raise HTTPException(status_code=404, detail="策略配置不存在")
    next_version = config.latest_version_number + 1
    db.add(_make_version(config.id, next_version, payload))
    config.latest_version_number = next_version
    db.commit()
    db.refresh(config)
    return _config_response(db, config)


@router.post(
    "/{config_id}/backtests",
    response_model=BacktestResponse,
    status_code=status.HTTP_201_CREATED,
)
def run_strategy_config_backtest(
    config_id: str,
    payload: StrategyConfigBacktestCreate,
    db: Session = Depends(get_db),
    identity: tuple[User, UserWallet, UserSession] = Depends(get_current_identity),
    settings: Settings = Depends(get_settings),
):
    user, _, _ = identity
    config = _owned_config(db, config_id, user.id)
    version_number = payload.version_number or config.latest_version_number
    version = db.scalar(
        select(StrategyConfigVersion).where(
            StrategyConfigVersion.config_id == config.id,
            StrategyConfigVersion.version_number == version_number,
        )
    )
    if version is None:
        raise HTTPException(status_code=404, detail="策略配置版本不存在")
    backtest = BacktestCreate.model_validate(
        {
            "strategy_name": version.strategy_name,
            "strategy_version": version.strategy_version,
            "exchange": version.exchange,
            "symbol": version.symbol,
            "timeframe": version.timeframe,
            "days": version.days,
            "parameters": version.parameters,
            "risk": version.risk_config,
            "execution": version.execution_config,
        }
    )
    return create_and_dispatch_backtest(
        db,
        owner_id=user.id,
        payload=backtest,
        settings=settings,
        strategy_config_version_id=version.id,
    )
