"""Convoy API - Simplified batch processing."""

from fastapi import FastAPI

from src.api.routes import router
from src.api.management_routes import management_router

app = FastAPI(
    title="🚂 Convoy API",
    description="Simplified batch processing with project-level authentication",
    version="0.2.0",
)

# Include cargo operations routes (require project API key)
app.include_router(router)

# Include management routes (require admin API key)
app.include_router(management_router)
