from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime
from .models import StageEnum, DeploymentStatusEnum

# --- Metrics ---

class MetricBase(BaseModel):
    version: Optional[str] = None
    environment: Optional[str] = None
    latency: Optional[float] = None
    throughput: Optional[float] = None
    error_rate: Optional[float] = None
    quality_score: Optional[float] = None
    drift_score: Optional[float] = None
    availability: Optional[float] = None

class MetricCreate(MetricBase):
    pass

class Metric(MetricBase):
    id: int
    model_id: str
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Model Versions ---

class ModelVersionBase(BaseModel):
    version: str
    stage: StageEnum = StageEnum.DRAFT
    approved: bool = False
    artifact_uri: Optional[str] = None

class ModelVersionCreate(ModelVersionBase):
    pass

class ModelVersion(ModelVersionBase):
    id: int
    model_id: str

    model_config = ConfigDict(from_attributes=True)

# --- Models ---

class ModelBase(BaseModel):
    id: str
    name: str
    owner: str
    framework: str

class ModelCreate(ModelBase):
    pass

class Model(ModelBase):
    versions: List[ModelVersion] = []

    model_config = ConfigDict(from_attributes=True)

# --- Deployments ---

class DeploymentBase(BaseModel):
    model_version_id: int
    environment: str

class DeploymentCreate(DeploymentBase):
    simulate_failure: bool = False

class Deployment(DeploymentBase):
    id: str
    status: DeploymentStatusEnum
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
