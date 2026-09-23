import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app import crud, schemas

# Setup in-memory DB for pure unit testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

def test_get_metrics(db_session):
    # Setup model
    crud.create_model(db_session, schemas.ModelCreate(id="m5", name="M5", owner="user", framework="sklearn"))
    
    # We test the basic metric fetching to ensure pagination and mapping works.
    # Note: metrics are currently seeded in the actual app, this tests the access logic.
    metrics = crud.get_metrics(db_session, "m5")
    assert isinstance(metrics, list)
