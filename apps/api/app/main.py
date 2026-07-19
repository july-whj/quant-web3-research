from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.router import api_router
from .core.config import get_settings
from .db.base import Base
from .db.session import engine
from . import models  # noqa: F401  Ensures SQLAlchemy mappings are registered.


settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings.artifact_dir.mkdir(parents=True, exist_ok=True)
    if settings.create_tables_on_startup:
        Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Open-source Web3 quantitative research API. Research only; no live trading endpoints.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-Admin-Key"],
)
app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/", include_in_schema=False)
def root() -> dict[str, str]:
    return {"service": "quant-web3-research-api", "docs": "/docs"}
