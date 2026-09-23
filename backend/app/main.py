from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import health, models, deployments

app = FastAPI(
    title="MLOps Platform Seed API",
    version="0.1.0"
)

# CORS config
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Should be restricted in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(models.router)
app.include_router(deployments.router)
