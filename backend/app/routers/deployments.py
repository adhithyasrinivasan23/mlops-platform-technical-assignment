from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import time
import random

from .. import crud, schemas
from ..database import get_db, SessionLocal
from ..models import Deployment, DeploymentStatusEnum

router = APIRouter(prefix="/deployments", tags=["deployments"])

@router.get("", response_model=List[schemas.Deployment])
def read_deployments(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_deployments(db, skip=skip, limit=limit)

def simulate_deployment(deployment_id: str, simulate_failure: bool = False):
    db = SessionLocal()
    try:
        deployment = db.query(Deployment).filter(Deployment.id == deployment_id).first()
        if not deployment:
            return
            
        time.sleep(3)
        deployment.status = DeploymentStatusEnum.VALIDATING
        db.commit()
        
        time.sleep(3)
        deployment.status = DeploymentStatusEnum.DEPLOYING
        db.commit()
        
        time.sleep(4)
        if simulate_failure:
            deployment.status = DeploymentStatusEnum.FAILED
        elif random.random() < 0.8:
            deployment.status = DeploymentStatusEnum.SUCCEEDED
        else:
            deployment.status = DeploymentStatusEnum.FAILED
        db.commit()
    finally:
        db.close()

@router.post("", response_model=schemas.Deployment, status_code=202)
def create_deployment(deployment: schemas.DeploymentCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    db_deployment = crud.create_deployment(db=db, deployment=deployment)
    background_tasks.add_task(simulate_deployment, db_deployment.id, deployment.simulate_failure)
    return db_deployment

@router.get("/{deployment_id}", response_model=schemas.Deployment)
def read_deployment(deployment_id: str, db: Session = Depends(get_db)):
    db_deployment = crud.get_deployment(db, deployment_id=deployment_id)
    if db_deployment is None:
        raise HTTPException(status_code=404, detail="Deployment not found")
    return db_deployment

@router.post("/{deployment_id}/retry", response_model=schemas.Deployment)
def retry_deployment(deployment_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    db_deployment = crud.retry_deployment(db=db, deployment_id=deployment_id)
    background_tasks.add_task(simulate_deployment, db_deployment.id)
    return db_deployment

@router.post("/{deployment_id}/rollback", response_model=schemas.Deployment)
def rollback_deployment(deployment_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    db_deployment = crud.rollback_deployment(db=db, deployment_id=deployment_id)
    # The rollback creates a new REQUESTED deployment (the returned db_deployment)
    if db_deployment.status == DeploymentStatusEnum.REQUESTED:
        background_tasks.add_task(simulate_deployment, db_deployment.id)
    return db_deployment
