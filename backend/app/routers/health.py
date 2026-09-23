from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from sqlalchemy import text

router = APIRouter(tags=["health"])

@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    # Basic check to ensure DB is connected
    try:
        db.execute(text("SELECT 1"))
        return {"status": "Healthy"}
    except Exception as e:
        return {"status": "Unhealthy", "details": str(e)}
