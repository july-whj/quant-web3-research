from fastapi import APIRouter

from .routes import analytics, auth, backtests, datasets, health, strategies


api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(strategies.router)
api_router.include_router(datasets.router)
api_router.include_router(backtests.router)
api_router.include_router(analytics.router)
