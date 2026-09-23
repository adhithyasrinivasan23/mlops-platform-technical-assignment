"""
conftest.py — shared pytest fixtures.

Key responsibilities:
1. Ensure the `simulate_deployment` background task uses the same in-memory
   SQLite session as the rest of the test suite (not the real PostgreSQL
   SessionLocal).
2. Disable `simulate_deployment` entirely during unit/integration tests.
   FastAPI's TestClient runs BackgroundTasks *synchronously* after the
   response is returned, so without this patch the deployment sleeps 10s and
   transitions to SUCCEEDED/FAILED before any test assertion runs.
"""
import pytest
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


@pytest.fixture(autouse=True)
def patch_deployment_internals():
    """
    - Patch SessionLocal so the background task uses SQLite, not PostgreSQL.
    - Patch simulate_deployment to a no-op so deployment status stays at
      REQUESTED after POST /deployments (tests manipulate state directly).
    """
    with patch("app.routers.deployments.SessionLocal", TestingSessionLocal), \
         patch("app.routers.deployments.simulate_deployment", lambda *args, **kwargs: None):
        yield

