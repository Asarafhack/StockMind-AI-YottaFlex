import os
import json
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from backend.app.database import get_db
from data_engine.validators.data_validator import DataValidator

router = APIRouter(prefix="/validation", tags=["Data Validation & Quality"])

@router.post("/run")
def trigger_data_validation(db: Session = Depends(get_db)) -> Dict[str, Any]:
    validator = DataValidator(db)
    report = validator.run_full_validation()
    return report

@router.get("/reports")
def get_validation_reports(db: Session = Depends(get_db)) -> Dict[str, Any]:
    validator = DataValidator(db)
    return validator.run_full_validation()

@router.get("/exports/list")
def list_available_exports() -> Dict[str, Any]:
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    exports_dir = os.path.join(base_dir, "output", "exports")
    gt_dir = os.path.join(base_dir, "output", "ground_truth")

    exported_files = []
    if os.path.exists(exports_dir):
        for f in os.listdir(exports_dir):
            p = os.path.join(exports_dir, f)
            exported_files.append({
                "filename": f,
                "type": f.split(".")[-1].upper(),
                "size_bytes": os.path.getsize(p),
                "path": p
            })

    gt_files = []
    if os.path.exists(gt_dir):
        for f in os.listdir(gt_dir):
            p = os.path.join(gt_dir, f)
            gt_files.append({
                "filename": f,
                "size_bytes": os.path.getsize(p),
                "path": p
            })

    return {
        "exports_count": len(exported_files),
        "exported_files": exported_files,
        "ground_truth_files": gt_files
    }
