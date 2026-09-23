"""
conftest.py — shared pytest fixtures.

Key responsibility: ensure the `simulate_deployment` background task uses the
same in-memory SQLite session as the rest of the test suite, not the real
PostgreSQL SessionLocal. Without this patch, any test that triggers
POST /deployments will fail in CI because the background task tries to open
a connection to localhost:5432.
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
def patch_deployment_session():
    """Patch the SessionLocal used inside simulate_deployment so it uses SQLite."""
    with patch("app.routers.deployments.SessionLocal", TestingSessionLocal):
        yield
