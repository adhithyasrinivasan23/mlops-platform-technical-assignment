import uuid
from sqlalchemy.orm import Session
from fastapi import HTTPException
from . import models, schemas

# --- Models ---

def get_model(db: Session, model_id: str):
    return db.query(models.Model).filter(models.Model.id == model_id).first()

def get_models(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Model).offset(skip).limit(limit).all()

def create_model(db: Session, model: schemas.ModelCreate):
    db_model = models.Model(**model.model_dump())
    db.add(db_model)
    db.commit()
    db.refresh(db_model)
    return db_model

# --- Model Versions ---

def get_model_versions(db: Session, model_id: str, skip: int = 0, limit: int = 100):
    return db.query(models.ModelVersion).filter(models.ModelVersion.model_id == model_id).offset(skip).limit(limit).all()

def get_model_version(db: Session, model_id: str, version: str):
    return db.query(models.ModelVersion).filter(
        models.ModelVersion.model_id == model_id,
        models.ModelVersion.version == version
    ).first()

def create_model_version(db: Session, model_id: str, version: schemas.ModelVersionCreate):
    db_model = get_model(db, model_id)
    if not db_model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    db_version = models.ModelVersion(**version.model_dump(), model_id=model_id)
    db.add(db_version)
    db.commit()
    db.refresh(db_version)
    return db_version

def approve_model_version(db: Session, version_id: int):
    db_version = db.query(models.ModelVersion).filter(models.ModelVersion.id == version_id).first()
    if db_version:
        db_version.approved = True
        if db_version.stage in [models.StageEnum.DRAFT, models.StageEnum.VALIDATED]:
            db_version.stage = models.StageEnum.APPROVED
        db.commit()
        db.refresh(db_version)
    return db_version

def archive_model_version(db: Session, version_id: int):
    db_version = db.query(models.ModelVersion).filter(models.ModelVersion.id == version_id).first()
    if db_version:
        db_version.stage = models.StageEnum.ARCHIVED
        db.commit()
        db.refresh(db_version)
    return db_version

# --- Deployments ---

def get_deployments(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Deployment).offset(skip).limit(limit).all()

def get_deployment(db: Session, deployment_id: str):
    return db.query(models.Deployment).filter(models.Deployment.id == deployment_id).first()

def create_deployment(db: Session, deployment: schemas.DeploymentCreate):
    # Idempotency check: Is this exact version already deployed/deploying to this environment?
    existing = db.query(models.Deployment).filter(
        models.Deployment.model_version_id == deployment.model_version_id,
        models.Deployment.environment == deployment.environment,
        models.Deployment.status.in_([models.DeploymentStatusEnum.REQUESTED, models.DeploymentStatusEnum.VALIDATING, models.DeploymentStatusEnum.DEPLOYING, models.DeploymentStatusEnum.SUCCEEDED])
    ).first()
    if existing:
        return existing
        
    db_version = db.query(models.ModelVersion).filter(models.ModelVersion.id == deployment.model_version_id).first()
    if not db_version:
        raise HTTPException(status_code=404, detail="Model version not found")

    if not db_version.approved:
        raise HTTPException(status_code=400, detail="Cannot deploy an unapproved model version")
    if db_version.stage == models.StageEnum.ARCHIVED:
        raise HTTPException(status_code=400, detail="Cannot deploy an archived model version")

    # Idempotency: if an in-flight deployment already exists for this version+environment, return it
    in_flight_statuses = [
        models.DeploymentStatusEnum.REQUESTED,
        models.DeploymentStatusEnum.VALIDATING,
        models.DeploymentStatusEnum.DEPLOYING,
    ]
    existing = db.query(models.Deployment).filter(
        models.Deployment.model_version_id == deployment.model_version_id,
        models.Deployment.environment == deployment.environment,
        models.Deployment.status.in_(in_flight_statuses)
    ).first()
    if existing:
        return existing

    deployment_id = f"dep-{uuid.uuid4().hex[:8]}"
    db_deployment = models.Deployment(
        id=deployment_id,
        model_version_id=deployment.model_version_id,
        environment=deployment.environment,
        status=models.DeploymentStatusEnum.REQUESTED
    )
    db.add(db_deployment)
    db.commit()
    db.refresh(db_deployment)
    return db_deployment

def update_deployment_status(db: Session, deployment_id: str, status: models.DeploymentStatusEnum):
    db_deployment = get_deployment(db, deployment_id)
    if not db_deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    db_deployment.status = status
    db.commit()
    db.refresh(db_deployment)
    return db_deployment

def retry_deployment(db: Session, deployment_id: str):
    db_deployment = get_deployment(db, deployment_id)
    if not db_deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    if db_deployment.status != models.DeploymentStatusEnum.FAILED:
        raise HTTPException(status_code=400, detail="Can only retry FAILED deployments")
    db_deployment.status = models.DeploymentStatusEnum.REQUESTED
    db.commit()
    db.refresh(db_deployment)
    return db_deployment

def rollback_deployment(db: Session, deployment_id: str):
    db_deployment = get_deployment(db, deployment_id)
    if not db_deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    if db_deployment.status != models.DeploymentStatusEnum.SUCCEEDED:
        raise HTTPException(status_code=400, detail="Can only rollback SUCCEEDED deployments")
    db_deployment.status = models.DeploymentStatusEnum.ROLLED_BACK
    db.commit()

    model_id = db_deployment.model_version.model_id
    previous_deployment = db.query(models.Deployment).join(models.ModelVersion).filter(
        models.ModelVersion.model_id == model_id,
        models.Deployment.environment == db_deployment.environment,
        models.Deployment.status == models.DeploymentStatusEnum.SUCCEEDED,
        models.Deployment.id != deployment_id,
        models.Deployment.created_at < db_deployment.created_at
    ).order_by(models.Deployment.created_at.desc()).first()

    if previous_deployment:
        new_dep_id = f"dep-{uuid.uuid4().hex[:8]}"
        new_deployment = models.Deployment(
            id=new_dep_id,
            model_version_id=previous_deployment.model_version_id,
            environment=db_deployment.environment,
            status=models.DeploymentStatusEnum.REQUESTED
        )
        db.add(new_deployment)
        db.commit()
        db.refresh(new_deployment)
        return new_deployment
    else:
        db.refresh(db_deployment)
        return db_deployment

# --- Metrics ---

def get_metrics(db: Session, model_id: str, skip: int = 0, limit: int = 100):
    return db.query(models.Metric).filter(models.Metric.model_id == model_id).offset(skip).limit(limit).all()
