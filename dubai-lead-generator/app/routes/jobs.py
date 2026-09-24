"""
Job management endpoints.
"""

import uuid
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.database import repositories as repo
from app.services.discovery import DiscoveryService, set_job_state
from app.config import settings
from app.utils.auth import get_current_admin

router = APIRouter(prefix="/jobs", tags=["jobs"])

# In-memory run registry
_ACTIVE_RUNS: dict = {}


class StartJobRequest(BaseModel):
    areas: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    city: Optional[str] = "Dubai"
    country: Optional[str] = "United Arab Emirates"
    max_businesses: Optional[int] = None
    min_lead_score: Optional[int] = None


def _run_discovery(run_id: str, request: StartJobRequest, db: Session):
    """Background task function for running discovery."""
    try:
        service = DiscoveryService(db)
        result = service.start_run(
            run_id=run_id,
            areas=request.areas,
            categories=request.categories,
            city=request.city or "Dubai",
            country=request.country or "United Arab Emirates",
            max_businesses=request.max_businesses,
        )
        _ACTIVE_RUNS[run_id] = {"status": "completed", "result": result}
    except Exception as exc:
        _ACTIVE_RUNS[run_id] = {"status": "failed", "error": str(exc)}
    finally:
        db.close()


@router.post("/start")
def start_job(
    request: StartJobRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """Start a new discovery run in the background."""
    run_id = str(uuid.uuid4())
    _ACTIVE_RUNS[run_id] = {"status": "running", "started_at": datetime.utcnow().isoformat()}

    # Use a new DB session for the background task
    from app.database.db import SessionLocal
    bg_db = SessionLocal()
    background_tasks.add_task(_run_discovery, run_id, request, bg_db)

    return {
        "run_id": run_id,
        "status": "started",
        "message": "Discovery run started in background.",
        "areas": request.areas,
        "categories": request.categories,
    }


@router.get("")
def list_jobs(
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List all search jobs."""
    jobs = repo.get_jobs(db, skip=skip, limit=limit, status=status)
    return {
        "total": len(jobs),
        "jobs": [j.to_dict() for j in jobs],
        "active_runs": list(_ACTIVE_RUNS.keys()),
    }


@router.get("/runs/{run_id}")
def get_run_status(run_id: str):
    """Get the status of a discovery run."""
    if run_id not in _ACTIVE_RUNS:
        raise HTTPException(status_code=404, detail="Run not found.")
    return _ACTIVE_RUNS[run_id]


@router.get("/{job_id}")
def get_job(job_id: str, db: Session = Depends(get_db)):
    """Get details of a specific search job."""
    job = repo.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return job.to_dict()


@router.post("/{job_id}/pause")
def pause_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """Pause a running job."""
    job = repo.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    set_job_state(job_id, "paused")
    repo.update_job(db, job_id, {"status": "paused"})
    return {"job_id": job_id, "status": "paused"}


@router.post("/{job_id}/resume")
def resume_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """Resume a paused job."""
    job = repo.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    set_job_state(job_id, "running")
    repo.update_job(db, job_id, {"status": "running"})
    return {"job_id": job_id, "status": "resumed"}


@router.post("/{job_id}/cancel")
def cancel_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """Cancel a job."""
    job = repo.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    set_job_state(job_id, "cancelled")
    repo.update_job(db, job_id, {"status": "cancelled", "completed_at": datetime.utcnow()})
    return {"job_id": job_id, "status": "cancelled"}


@router.post("/{job_id}/retry")
def retry_job(
    job_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """Retry a failed job."""
    job = repo.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    if job.status not in ("failed", "cancelled"):
        raise HTTPException(status_code=400, detail=f"Job status is '{job.status}', cannot retry.")

    run_id = str(uuid.uuid4())
    request = StartJobRequest(
        areas=[job.area],
        categories=[job.category],
    )
    _ACTIVE_RUNS[run_id] = {"status": "running", "retried_job": job_id}

    from app.database.db import SessionLocal
    bg_db = SessionLocal()
    background_tasks.add_task(_run_discovery, run_id, request, bg_db)

    return {"run_id": run_id, "retried_job_id": job_id, "status": "started"}
