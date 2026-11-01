from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from backend.app.database import get_db
from backend.app.models.entities import AnomalyRecord, AuditEvent
from backend.app.schemas.schemas import AnomalyResponse
from backend.app.services.anomaly_engine import AnomalyEngine
import datetime

router = APIRouter(prefix="/anomalies", tags=["Anomaly Center"])

@router.get("", response_model=List[AnomalyResponse])
def get_anomalies(
    issue_type: Optional[str] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    affected_sku: Optional[str] = None,
    affected_location: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    query = db.query(AnomalyRecord)
    if issue_type:
        query = query.filter(AnomalyRecord.issue_type == issue_type)
    if severity:
        query = query.filter(AnomalyRecord.severity == severity)
    if status:
        query = query.filter(AnomalyRecord.status == status)
    if affected_sku:
        query = query.filter(AnomalyRecord.affected_sku == affected_sku)
    if affected_location:
        query = query.filter(AnomalyRecord.affected_location == affected_location)

    return query.order_by(AnomalyRecord.detection_timestamp.desc()).offset(skip).limit(limit).all()

@router.get("/{anomaly_id}", response_model=AnomalyResponse)
def get_anomaly_detail(anomaly_id: str, db: Session = Depends(get_db)):
    anom = db.query(AnomalyRecord).filter(AnomalyRecord.anomaly_id == anomaly_id).first()
    if not anom:
        raise HTTPException(status_code=404, detail="Anomaly not found")
    return anom

@router.post("/scan")
def trigger_anomaly_scan(db: Session = Depends(get_db)):
    engine = AnomalyEngine(db)
    detected = engine.scan_all_anomalies(persist=True)
    return {
        "status": "SCAN_COMPLETE",
        "total_anomalies_detected": len(detected),
        "anomalies": [
            {
                "anomaly_id": a.anomaly_id,
                "issue_type": a.issue_type,
                "entity_id": a.entity_id,
                "severity": a.severity
            } for a in detected
        ]
    }

@router.post("/{anomaly_id}/acknowledge")
def acknowledge_anomaly(
    anomaly_id: str,
    operator: str = "OPERATOR_ADMIN",
    db: Session = Depends(get_db)
):
    anom = db.query(AnomalyRecord).filter(AnomalyRecord.anomaly_id == anomaly_id).first()
    if not anom:
        raise HTTPException(status_code=404, detail="Anomaly not found")
    anom.status = "ACKNOWLEDGED"

    audit = AuditEvent(
        audit_id=f"AUD-{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}",
        timestamp=datetime.datetime.utcnow(),
        event_type="ANOMALY_ACKNOWLEDGED",
        entity_type="AnomalyRecord",
        entity_id=anom.anomaly_id,
        action="ACKNOWLEDGE",
        user_id=operator,
        details=f"Acknowledged {anom.issue_type} on {anom.entity_id}"
    )
    db.add(audit)
    db.commit()
    return {"status": "SUCCESS", "anomaly_status": anom.status}

@router.post("/{anomaly_id}/resolve")
def resolve_anomaly(
    anomaly_id: str,
    resolution_notes: str = "RESOLVED_BY_OPERATOR",
    operator: str = "OPERATOR_ADMIN",
    db: Session = Depends(get_db)
):
    anom = db.query(AnomalyRecord).filter(AnomalyRecord.anomaly_id == anomaly_id).first()
    if not anom:
        raise HTTPException(status_code=404, detail="Anomaly not found")

    now = datetime.datetime.utcnow()
    anom.status = "RESOLVED"
    anom.resolved_at = now
    anom.resolved_by = operator

    audit = AuditEvent(
        audit_id=f"AUD-{now.strftime('%Y%m%d%H%M%S%f')}",
        timestamp=now,
        event_type="ANOMALY_RESOLVED",
        entity_type="AnomalyRecord",
        entity_id=anom.anomaly_id,
        action="RESOLVE",
        user_id=operator,
        details=f"Resolved {anom.issue_type}: {resolution_notes}"
    )
    db.add(audit)
    db.commit()
    return {"status": "SUCCESS", "anomaly_status": anom.status, "resolved_at": now.isoformat()}
