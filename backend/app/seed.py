import json
import csv
import os
from datetime import datetime
from sqlalchemy.orm import Session
from app.database import engine, SessionLocal
from app.models import Model, ModelVersion, Deployment, Metric, StageEnum, DeploymentStatusEnum

def load_models(db: Session, artifacts_dir: str):
    file_path = os.path.join(artifacts_dir, 'sample_model_registry.json')
    if not os.path.exists(file_path):
        print(f"Skipping models seed: {file_path} not found")
        return

    with open(file_path, 'r') as f:
        data = json.load(f)
        for item in data:
            model_id = item["model_id"]
            # Check if model exists
            model = db.query(Model).filter(Model.id == model_id).first()
            if not model:
                model = Model(
                    id=model_id,
                    name=item["name"],
                    owner=item["owner"],
                    framework=item["framework"]
                )
                db.add(model)
                db.commit()
                db.refresh(model)

            # Insert versions
            for v_data in item.get("versions", []):
                version_str = v_data["version"]
                version = db.query(ModelVersion).filter(
                    ModelVersion.model_id == model.id,
                    ModelVersion.version == version_str
                ).first()
                if not version:
                    version = ModelVersion(
                        model_id=model.id,
                        version=version_str,
                        stage=StageEnum(v_data["stage"]),
                        approved=v_data["approved"],
                        artifact_uri=v_data.get("artifact_uri")
                    )
                    db.add(version)
                    db.commit()

def load_deployments(db: Session, artifacts_dir: str):
    file_path = os.path.join(artifacts_dir, 'sample_deployment_events.json')
    if not os.path.exists(file_path):
        print(f"Skipping deployments seed: {file_path} not found")
        return

    with open(file_path, 'r') as f:
        data = json.load(f)
        for item in data:
            dep_id = item["deployment_id"]
            
            # Check if exists
            deployment = db.query(Deployment).filter(Deployment.id == dep_id).first()
            if not deployment:
                # Find the ModelVersion
                model_id = item["model_id"]
                version_str = item["version"]

                model = db.query(Model).filter(Model.id == model_id).first()
                if not model:
                    model = Model(id=model_id, name=model_id, owner="Unknown", framework="Unknown")
                    db.add(model)
                    db.commit()

                version = db.query(ModelVersion).filter(
                    ModelVersion.model_id == model_id,
                    ModelVersion.version == version_str
                ).first()
                
                if not version:
                    version = ModelVersion(model_id=model_id, version=version_str, stage=StageEnum.PRODUCTION, approved=True)
                    db.add(version)
                    db.commit()

                if version:
                    dt = datetime.strptime(item["timestamp"], "%Y-%m-%dT%H:%M:%SZ")
                    deployment = Deployment(
                        id=dep_id,
                        model_version_id=version.id,
                        environment=item["environment"],
                        status=DeploymentStatusEnum(item["status"]),
                        created_at=dt,
                        updated_at=dt
                    )
                    db.add(deployment)
                    db.commit()

def load_metrics(db: Session, artifacts_dir: str):
    file_path = os.path.join(artifacts_dir, 'sample_model_metrics.csv')
    if not os.path.exists(file_path):
        print(f"Skipping metrics seed: {file_path} not found")
        return

    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            model_id = row["model_id"]
            model_exists = db.query(Model).filter(Model.id == model_id).first()
            if not model_exists:
                model = Model(id=model_id, name=model_id, owner="Unknown", framework="Unknown")
                db.add(model)
                db.commit()

            if count == 0:
                existing = db.query(Metric).filter(Metric.model_id == model_id).first()
                if existing:
                    print(f"Metrics already seeded for model {model_id}, skipping.")
                    continue
            
            dt = datetime.strptime(row["timestamp"], "%Y-%m-%dT%H:%M:%SZ")
            metric = Metric(
                model_id=model_id,
                timestamp=dt,
                version=row.get("version"),
                environment=row.get("environment"),
                latency=float(row["latency_ms"]) if row["latency_ms"] else None,
                throughput=float(row["throughput_rpm"]) if row["throughput_rpm"] else None,
                error_rate=float(row["error_rate"]) if row["error_rate"] else None,
                quality_score=float(row["quality_score"]) if row["quality_score"] else None,
                drift_score=float(row["drift_score"]) if row["drift_score"] else None,
                availability=float(row["availability"]) if row["availability"] else None
            )
            db.add(metric)
            count += 1
            if count % 100 == 0:
                db.commit()
        db.commit()

def main():
    print("Starting database seeding...")
    artifacts_dir = os.environ.get("ARTIFACTS_DIR", "/app/data")
    if not os.path.exists(artifacts_dir):
        # Fallback for local execution outside of Docker
        artifacts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data"))
    
    db = SessionLocal()
    try:
        load_models(db, artifacts_dir)
        load_deployments(db, artifacts_dir)
        load_metrics(db, artifacts_dir)
        print("Database seeding completed.")
    except Exception as e:
        print(f"Error seeding database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
