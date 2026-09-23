import enum
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Float, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class StageEnum(str, enum.Enum):
    DRAFT = "DRAFT"
    VALIDATED = "VALIDATED"
    APPROVED = "APPROVED"
    STAGING = "STAGING"
    PRODUCTION = "PRODUCTION"
    ARCHIVED = "ARCHIVED"

class DeploymentStatusEnum(str, enum.Enum):
    REQUESTED = "REQUESTED"
    VALIDATING = "VALIDATING"
    DEPLOYING = "DEPLOYING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    ROLLED_BACK = "ROLLED_BACK"

class Model(Base):
    __tablename__ = "models"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    owner = Column(String)
    framework = Column(String)

    versions = relationship("ModelVersion", back_populates="model", cascade="all, delete-orphan")
    metrics = relationship("Metric", back_populates="model", cascade="all, delete-orphan")

class ModelVersion(Base):
    __tablename__ = "model_versions"

    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(String, ForeignKey("models.id"))
    version = Column(String)
    stage = Column(Enum(StageEnum), default=StageEnum.DRAFT)
    approved = Column(Boolean, default=False)
    artifact_uri = Column(String)

    model = relationship("Model", back_populates="versions")
    deployments = relationship("Deployment", back_populates="model_version", cascade="all, delete-orphan")

class Deployment(Base):
    __tablename__ = "deployments"

    id = Column(String, primary_key=True, index=True)
    model_version_id = Column(Integer, ForeignKey("model_versions.id"))
    environment = Column(String)
    status = Column(Enum(DeploymentStatusEnum), default=DeploymentStatusEnum.REQUESTED)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    model_version = relationship("ModelVersion", back_populates="deployments")

class Metric(Base):
    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(String, ForeignKey("models.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    version = Column(String, nullable=True)
    environment = Column(String, nullable=True)
    latency = Column(Float, nullable=True)
    throughput = Column(Float, nullable=True)
    error_rate = Column(Float, nullable=True)
    quality_score = Column(Float, nullable=True)
    drift_score = Column(Float, nullable=True)
    availability = Column(Float, nullable=True)

    model = relationship("Model", back_populates="metrics")
