"""
FastAPI application entrypoint.
Mounts routes, static dashboard, scheduler, and database init.
"""

import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from loguru import logger

from app.database.db import init_db
from app.routes.health import router as health_router
from app.routes.jobs import router as jobs_router
from app.routes.leads import router as leads_router
from app.routes.sync import router as sync_router
from app.routes.auth import router as auth_router
from app.routes.webhooks import router as webhooks_router
from app.config import settings, yaml_config
from app.utils.logger import setup_logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    # Startup
    setup_logger()
    logger.info("Dubai Business Lead Generator starting up...")
    logger.info(f"Config: {settings.safe_repr()}")
    init_db()

    # Optional APScheduler
    scheduler = None
    if yaml_config.scheduler_config.get("enabled", False):
        try:
            from apscheduler.schedulers.asyncio import AsyncIOScheduler
            from apscheduler.triggers.cron import CronTrigger
            from app.database.db import SessionLocal
            from app.services.discovery import DiscoveryService

            scheduler = AsyncIOScheduler()
            cron_expr = yaml_config.scheduler_config.get("cron", "0 10 * * *")
            parts = cron_expr.strip().split()

            async def scheduled_run():
                logger.info("Scheduled discovery run starting...")
                db = SessionLocal()
                try:
                    svc = DiscoveryService(db)
                    svc.start_run(run_id=str(uuid.uuid4()))
                finally:
                    db.close()

            scheduler.add_job(
                scheduled_run,
                CronTrigger(
                    minute=parts[0],
                    hour=parts[1],
                    day=parts[2],
                    month=parts[3],
                    day_of_week=parts[4],
                ),
            )
            scheduler.start()
            logger.info(f"Scheduler started with cron: {cron_expr}")
        except Exception as exc:
            logger.error(f"Scheduler startup failed: {exc}")

    yield

    # Shutdown
    if scheduler:
        scheduler.shutdown()
    logger.info("Dubai Business Lead Generator shut down.")


app = FastAPI(
    title="Dubai Business Lead Generator",
    description="Automated Dubai business discovery and lead qualification system.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Configuration
if settings.app_env == "production":
    allowed_origins = [o.strip() for o in settings.frontend_origin.split(",") if o.strip()]
    if not allowed_origins:
        allowed_origins = ["http://localhost:3000"]
    allow_origins_list = allowed_origins
else:
    # Development: Allow local dev ports and frontend origins
    allow_origins_list = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    if settings.frontend_origin:
        for o in settings.frontend_origin.split(","):
            if o.strip() and o.strip() not in allow_origins_list:
                allow_origins_list.append(o.strip())

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Production security response headers."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if settings.app_env == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


# Routes
app.include_router(health_router)
app.include_router(jobs_router)
app.include_router(leads_router)
app.include_router(sync_router)
app.include_router(auth_router)
app.include_router(webhooks_router)

dashboard_dir = Path(__file__).resolve().parent.parent / "dashboard"
if dashboard_dir.exists():
    app.mount("/dashboard", StaticFiles(directory=str(dashboard_dir), html=True), name="dashboard")

    @app.get("/", include_in_schema=False)
    def root():
        return FileResponse(str(dashboard_dir / "index.html"))

    @app.get("/demo/{lead_id}", include_in_schema=False)
    def live_demo_redirect(lead_id: str):
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=f"/leads/{lead_id}/demo")
else:
    @app.get("/", include_in_schema=False)
    def root():
        return {
            "message": "Dubai Business Lead Generator API",
            "docs": "/docs",
            "health": "/health",
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug,
    )
