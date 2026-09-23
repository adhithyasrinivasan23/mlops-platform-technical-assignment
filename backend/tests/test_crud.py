import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app import crud, schemas, models

# Setup in-memory DB for pure unit testing of CRUD operations
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

def test_approve_model_version_logic(db_session):
    # Setup
    model_create = schemas.ModelCreate(id="m1", name="Model 1", owner="user", framework="sklearn")
    crud.create_model(db_session, model_create)
    version_create = schemas.ModelVersionCreate(version="1.0", stage="DRAFT", approved=False)
    v = crud.create_model_version(db_session, "m1", version_create)
    
    assert v.approved is False
    assert v.stage == models.StageEnum.DRAFT

    # Action
    approved_v = crud.approve_model_version(db_session, v.id)
    
    # Verify domain transition
    assert approved_v.approved is True
    assert approved_v.stage == models.StageEnum.APPROVED

def test_archive_model_version_logic(db_session):
    # Setup
    model_create = schemas.ModelCreate(id="m2", name="Model 2", owner="user", framework="sklearn")
    crud.create_model(db_session, model_create)
    version_create = schemas.ModelVersionCreate(version="1.0", stage="PRODUCTION", approved=True)
    v = crud.create_model_version(db_session, "m2", version_create)
    
    # Action
    archived_v = crud.archive_model_version(db_session, v.id)
    
    # Verify domain transition
    assert archived_v.stage == models.StageEnum.ARCHIVED
    assert archived_v.approved is True # Approval state remains, but stage is archived

def test_deployment_idempotency_logic(db_session):
    # Setup
    crud.create_model(db_session, schemas.ModelCreate(id="m3", name="M3", owner="user", framework="sklearn"))
    v = crud.create_model_version(db_session, "m3", schemas.ModelVersionCreate(version="1.0", stage="APPROVED", approved=True))
    
    dep_req = schemas.DeploymentCreate(model_version_id=v.id, environment="staging")
    dep1 = crud.create_deployment(db_session, dep_req)
    dep2 = crud.create_deployment(db_session, dep_req)
    
    # Second deployment should return the exact same deployment object
    assert dep1.id == dep2.id

def test_rollback_lookup_logic(db_session):
    # Setup
    crud.create_model(db_session, schemas.ModelCreate(id="m4", name="M4", owner="user", framework="sklearn"))
    v1 = crud.create_model_version(db_session, "m4", schemas.ModelVersionCreate(version="1.0", stage="APPROVED", approved=True))
    v2 = crud.create_model_version(db_session, "m4", schemas.ModelVersionCreate(version="2.0", stage="APPROVED", approved=True))
    
    # Dep 1 (v1) - SUCCEEDED
    dep1 = crud.create_deployment(db_session, schemas.DeploymentCreate(model_version_id=v1.id, environment="production"))
    crud.update_deployment_status(db_session, dep1.id, models.DeploymentStatusEnum.SUCCEEDED)
    
    # Dep 2 (v2) - SUCCEEDED (Latest)
    dep2 = crud.create_deployment(db_session, schemas.DeploymentCreate(model_version_id=v2.id, environment="production"))
    crud.update_deployment_status(db_session, dep2.id, models.DeploymentStatusEnum.SUCCEEDED)
    
    # Rollback dep2
    new_dep = crud.rollback_deployment(db_session, dep2.id)
    
    # Should create a new deployment request for v1
    assert new_dep.id != dep2.id
    assert new_dep.model_version_id == v1.id
    assert new_dep.status == models.DeploymentStatusEnum.REQUESTED
