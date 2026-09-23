import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app as fastapi_app
from app.database import Base, get_db
import app.models

# Re-use the same in-memory SQLite engine defined in conftest.py so that the
# test client and the patched simulate_deployment background task share state.
from tests.conftest import TestingSessionLocal, engine

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

fastapi_app.dependency_overrides[get_db] = override_get_db

client = TestClient(fastapi_app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "Healthy"}

def test_create_model():
    response = client.post(
        "/models",
        json={"id": "test-model-1", "name": "Test Model", "owner": "tester", "framework": "sklearn"}
    )
    assert response.status_code == 201
    assert response.json()["id"] == "test-model-1"

def test_create_deployment_unapproved_prod():
    # Setup model and unapproved version
    client.post(
        "/models",
        json={"id": "test-model-2", "name": "Test Model 2", "owner": "tester", "framework": "sklearn"}
    )
    version_res = client.post(
        "/models/test-model-2/versions",
        json={"version": "1.0.0", "stage": "DRAFT", "approved": False}
    )
    version_id = version_res.json()["id"]

    # Attempt to deploy to production
    response = client.post(
        "/deployments",
        json={"model_version_id": version_id, "environment": "production"}
    )
    assert response.status_code == 400
    assert "unapproved" in response.json()["detail"]

def test_get_nonexistent_model():
    response = client.get("/models/does-not-exist")
    assert response.status_code == 404

def test_create_duplicate_model():
    client.post(
        "/models",
        json={"id": "test-model-3", "name": "Test Model 3", "owner": "tester", "framework": "sklearn"}
    )
    response = client.post(
        "/models",
        json={"id": "test-model-3", "name": "Duplicate", "owner": "tester", "framework": "sklearn"}
    )
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]

def test_duplicate_deployment_idempotency():
    # Setup
    client.post(
        "/models",
        json={"id": "test-model-4", "name": "Test 4", "owner": "tester", "framework": "sklearn"}
    )
    version_res = client.post(
        "/models/test-model-4/versions",
        json={"version": "1.0.0", "stage": "STAGING", "approved": True}
    )
    version_id = version_res.json()["id"]

    # First deploy
    dep1 = client.post(
        "/deployments",
        json={"model_version_id": version_id, "environment": "staging"}
    )
    assert dep1.status_code == 202

    # Second deploy for same version+env while first is in-flight: must return same deployment
    dep2 = client.post(
        "/deployments",
        json={"model_version_id": version_id, "environment": "staging"}
    )
    assert dep2.status_code == 202
    assert dep1.json()["id"] == dep2.json()["id"]

def test_retry_deployment_rules():
    # Setup
    client.post(
        "/models",
        json={"id": "test-model-5", "name": "Test 5", "owner": "tester", "framework": "sklearn"}
    )
    version_res = client.post(
        "/models/test-model-5/versions",
        json={"version": "1.0.0", "stage": "STAGING", "approved": True}
    )
    version_id = version_res.json()["id"]
    
    dep_res = client.post(
        "/deployments",
        json={"model_version_id": version_id, "environment": "staging"}
    )
    dep_id = dep_res.json()["id"]

    # Cannot retry a REQUESTED deployment
    retry1 = client.post(f"/deployments/{dep_id}/retry")
    assert retry1.status_code == 400

    # Fail it directly in DB
    db = TestingSessionLocal()
    try:
        from app.crud import update_deployment_status
        from app.models import DeploymentStatusEnum
        update_deployment_status(db, dep_id, DeploymentStatusEnum.FAILED)
    finally:
        db.close()
    
    # Retry now should succeed
    retry2 = client.post(f"/deployments/{dep_id}/retry")
    assert retry2.status_code == 200
    assert retry2.json()["status"] == "REQUESTED"

def test_rollback_deployment_rules():
    # Setup
    client.post(
        "/models",
        json={"id": "test-model-6", "name": "Test 6", "owner": "tester", "framework": "sklearn"}
    )
    version_res = client.post(
        "/models/test-model-6/versions",
        json={"version": "1.0.0", "stage": "STAGING", "approved": True}
    )
    version_id = version_res.json()["id"]
    
    dep_res = client.post(
        "/deployments",
        json={"model_version_id": version_id, "environment": "staging"}
    )
    dep_id = dep_res.json()["id"]

    # Cannot rollback a REQUESTED deployment
    rollback1 = client.post(f"/deployments/{dep_id}/rollback")
    assert rollback1.status_code == 400

    # Succeed it directly in DB
    db = TestingSessionLocal()
    try:
        from app.crud import update_deployment_status
        from app.models import DeploymentStatusEnum
        update_deployment_status(db, dep_id, DeploymentStatusEnum.SUCCEEDED)
    finally:
        db.close()
    
    # Rollback now should succeed
    rollback2 = client.post(f"/deployments/{dep_id}/rollback")
    assert rollback2.status_code == 200
    assert rollback2.json()["status"] == "ROLLED_BACK"

def test_end_to_end_scenario():
    # 1. Register model
    model_res = client.post(
        "/models",
        json={"id": "pump-failure", "name": "Pump Failure", "owner": "AI Team", "framework": "sklearn"}
    )
    assert model_res.status_code == 201

    # 2. Register version
    version_res = client.post(
        "/models/pump-failure/versions",
        json={"version": "1.0.0"}
    )
    assert version_res.status_code == 201
    version_id = version_res.json()["id"]

    # 3. Approve version (Simulating by updating the DB)
    db = TestingSessionLocal()
    try:
        from app.models import ModelVersion
        v = db.query(ModelVersion).filter_by(id=version_id).first()
        v.approved = True
        v.stage = "PRODUCTION"
        db.commit()
    finally:
        db.close()

    # 4. Deploy to production
    dep_res = client.post(
        "/deployments",
        json={"model_version_id": version_id, "environment": "production"}
    )
    assert dep_res.status_code == 202
    dep_id = dep_res.json()["id"]

    # 5. View metrics (none initially, but we can verify endpoint works)
    metrics_res = client.get("/models/pump-failure/metrics")
    assert metrics_res.status_code == 200
    assert metrics_res.json() == []

    # 6. Roll back (First simulate success)
    db = TestingSessionLocal()
    try:
        from app.crud import update_deployment_status
        from app.models import DeploymentStatusEnum
        update_deployment_status(db, dep_id, DeploymentStatusEnum.SUCCEEDED)
    finally:
        db.close()
    
    rb_res = client.post(f"/deployments/{dep_id}/rollback")
    assert rb_res.status_code == 200
    assert rb_res.json()["status"] == "ROLLED_BACK"

def test_approve_version():
    client.post(
        "/models",
        json={"id": "test-approve", "name": "Test Approve", "owner": "tester", "framework": "sklearn"}
    )
    version_res = client.post(
        "/models/test-approve/versions",
        json={"version": "1.0.0", "stage": "DRAFT", "approved": False}
    )
    version_id = version_res.json()["id"]

    approve_res = client.post(f"/models/test-approve/versions/{version_id}/approve")
    assert approve_res.status_code == 200
    assert approve_res.json()["approved"] is True
    assert approve_res.json()["stage"] == "APPROVED"

def test_archive_version():
    client.post(
        "/models",
        json={"id": "test-archive", "name": "Test Archive", "owner": "tester", "framework": "sklearn"}
    )
    version_res = client.post(
        "/models/test-archive/versions",
        json={"version": "1.0.0", "stage": "STAGING", "approved": True}
    )
    version_id = version_res.json()["id"]

    archive_res = client.post(f"/models/test-archive/versions/{version_id}/archive")
    assert archive_res.status_code == 200
    assert archive_res.json()["stage"] == "ARCHIVED"

