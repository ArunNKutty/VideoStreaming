"""
Health check endpoints
"""
import time
from datetime import datetime
from fastapi import APIRouter
from app.models.video import HealthResponse
from app.core.config import settings

router = APIRouter(tags=["health"])

# Store startup time
startup_time = time.time()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    current_time = time.time()
    uptime = current_time - startup_time
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        version=settings.VERSION,
        uptime=uptime
    )


@router.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "description": settings.DESCRIPTION,
        "docs_url": "/docs",
        "health_url": f"{settings.API_V1_STR}/health"
    }
