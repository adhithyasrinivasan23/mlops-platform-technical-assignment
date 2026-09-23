from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from .. import crud, schemas
from ..database import get_db

router = APIRouter(prefix="/models", tags=["models"])

@router.get("", response_model=List[schemas.Model])
def read_models(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_models(db, skip=skip, limit=limit)

@router.post("", response_model=schemas.Model, status_code=201)
def create_model(model: schemas.ModelCreate, db: Session = Depends(get_db)):
    db_model = crud.get_model(db, model_id=model.id)
    if db_model:
        raise HTTPException(status_code=400, detail="Model already registered")
    return crud.create_model(db=db, model=model)

@router.get("/{model_id}", response_model=schemas.Model)
def read_model(model_id: str, db: Session = Depends(get_db)):
    db_model = crud.get_model(db, model_id=model_id)
    if db_model is None:
        raise HTTPException(status_code=404, detail="Model not found")
    return db_model

@router.get("/{model_id}/versions", response_model=List[schemas.ModelVersion])
def read_model_versions(model_id: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_model_versions(db, model_id=model_id, skip=skip, limit=limit)

@router.post("/{model_id}/versions", response_model=schemas.ModelVersion, status_code=201)
def create_model_version(model_id: str, version: schemas.ModelVersionCreate, db: Session = Depends(get_db)):
    db_version = crud.get_model_version(db, model_id=model_id, version=version.version)
    if db_version:
        raise HTTPException(status_code=400, detail="Version already exists")
    return crud.create_model_version(db=db, model_id=model_id, version=version)

@router.post("/{model_id}/versions/{version_id}/approve", response_model=schemas.ModelVersion)
def approve_model_version(model_id: str, version_id: int, db: Session = Depends(get_db)):
    db_version = crud.approve_model_version(db, version_id=version_id)
    if not db_version:
        raise HTTPException(status_code=404, detail="Version not found")
    return db_version

@router.post("/{model_id}/versions/{version_id}/archive", response_model=schemas.ModelVersion)
def archive_model_version(model_id: str, version_id: int, db: Session = Depends(get_db)):
    db_version = crud.archive_model_version(db, version_id=version_id)
    if not db_version:
        raise HTTPException(status_code=404, detail="Version not found")
    return db_version

@router.get("/{model_id}/metrics", response_model=List[schemas.Metric])
def read_model_metrics(model_id: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_metrics(db, model_id=model_id, skip=skip, limit=limit)
