"""
Health check and statistics endpoints.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.database.repositories import get_dashboard_stats, get_api_usage_today
from app.config import settings, yaml_config

router = APIRouter()


@router.get("/health")
def health_check():
    """Basic health check endpoint."""
    return {
        "status": "ok",
        "version": "1.0.0",
        "features": {
            "serpapi": settings.has_serpapi(),
            "gemini": settings.has_gemini() and settings.enable_gemini,
            "sheets": settings.has_sheets(),
            "reviews_enabled": settings.enable_reviews,
            "photos_enabled": settings.enable_photos,
            "posts_enabled": settings.enable_posts,
            "web_verification": settings.enable_web_verification,
            "free_mode": settings.free_mode,
        },
    }


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """Dashboard statistics."""
    stats = get_dashboard_stats(db)
    api_usage = get_api_usage_today(db)
    return {
        **stats,
        "config": settings.safe_repr(),
        "areas_configured": len(yaml_config.areas),
        "categories_configured": len(yaml_config.categories),
    }


@router.get("/config")
def get_config():
    """Return current safe configuration (no secrets)."""
    return {
        "areas": yaml_config.areas,
        "categories": yaml_config.categories,
        "lead_scoring": yaml_config.lead_scoring,
        "settings": settings.safe_repr(),
    }


@router.post("/config/areas")
def update_areas(areas: list[str]):
    """Update the list of target areas."""
    yaml_config.areas = areas
    yaml_config.save()
    return {"success": True, "areas": yaml_config.areas}


@router.post("/config/categories")
def update_categories(categories: list[str]):
    """Update the list of target categories."""
    yaml_config.categories = categories
    yaml_config.save()
    return {"success": True, "categories": yaml_config.categories}
