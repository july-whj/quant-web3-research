from __future__ import annotations

import os
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


database_file = Path(tempfile.gettempdir()) / "quant_web3_api_tests.db"
artifact_dir = Path(tempfile.gettempdir()) / "quant_web3_api_artifacts"
os.environ["DATABASE_URL"] = f"sqlite+pysqlite:///{database_file}"
os.environ["ARTIFACT_DIR"] = str(artifact_dir)
os.environ["CREATE_TABLES_ON_STARTUP"] = "false"
os.environ["JOB_MODE"] = "inline"
os.environ["ADMIN_API_KEY"] = "test-admin-key"

from apps.api.app import models  # noqa: E402, F401
from apps.api.app.db import Base, engine  # noqa: E402
from apps.api.app.main import app  # noqa: E402


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as test_client:
        yield test_client
