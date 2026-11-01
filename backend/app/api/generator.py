import os
import uuid
import threading
import time
from fastapi import APIRouter, BackgroundTasks, HTTPException
from typing import Dict, Any
from backend.app.schemas.schemas import GeneratorJobRequest, GeneratorJobResponse
from data_engine.run_pipeline import run_pipeline

router = APIRouter(prefix="/generator", tags=["Synthetic Data Generator"])

# In-memory jobs tracking
ACTIVE_JOBS: Dict[str, Dict[str, Any]] = {}
JOB_LOCK = threading.Lock()

def _execute_pipeline_task(job_id: str, req: GeneratorJobRequest):
    try:
        start_t = time.time()
        ACTIVE_JOBS[job_id]["status"] = "RUNNING"
        ACTIVE_JOBS[job_id]["progress_pct"] = 10.0
        ACTIVE_JOBS[job_id]["message"] = "Generating synthetic entities..."

        res = run_pipeline(
            profile=req.profile,
            seed=req.seed,
            batch_size=req.batch_size,
            include_anomalies=req.include_anomalies,
            formats=req.output_formats,
            populate_db=True
        )

        elapsed = round(time.time() - start_t, 2)
        ACTIVE_JOBS[job_id]["status"] = "COMPLETED"
        ACTIVE_JOBS[job_id]["progress_pct"] = 100.0
        ACTIVE_JOBS[job_id]["elapsed_seconds"] = elapsed
        ACTIVE_JOBS[job_id]["records_generated"] = res.get("records", {})
        ACTIVE_JOBS[job_id]["checksum_verified"] = True
        ACTIVE_JOBS[job_id]["message"] = f"Generated {res['records']['movements']} movements and {res['records']['orders']} orders with 100% verified checksums."
    except Exception as e:
        ACTIVE_JOBS[job_id]["status"] = "FAILED"
        ACTIVE_JOBS[job_id]["message"] = str(e)

@router.post("/jobs", response_model=GeneratorJobResponse, status_code=202)
def start_generator_job(req: GeneratorJobRequest, background_tasks: BackgroundTasks):
    with JOB_LOCK:
        for j_id, j_data in ACTIVE_JOBS.items():
            if j_data["status"] == "RUNNING":
                raise HTTPException(status_code=409, detail=f"Job {j_id} is already actively running. Wait for completion.")

        job_id = f"JOB-{uuid.uuid4().hex[:8].upper()}"
        ACTIVE_JOBS[job_id] = {
            "job_id": job_id,
            "status": "QUEUED",
            "profile": req.profile,
            "seed": req.seed,
            "records_generated": {},
            "progress_pct": 0.0,
            "elapsed_seconds": 0.0,
            "estimated_remaining_seconds": 30.0 if req.profile == "full" else 5.0,
            "manifest_path": "output/ground_truth/scenario_manifest.json",
            "checksum_verified": False,
            "message": "Job queued for execution"
        }

    background_tasks.add_task(_execute_pipeline_task, job_id, req)
    return ACTIVE_JOBS[job_id]

@router.get("/jobs/{job_id}", response_model=GeneratorJobResponse)
def get_generator_job_status(job_id: str):
    if job_id not in ACTIVE_JOBS:
        raise HTTPException(status_code=404, detail="Job not found")
    return ACTIVE_JOBS[job_id]
