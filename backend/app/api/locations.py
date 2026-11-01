from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.app.database import get_db
from backend.app.models.entities import Location
from backend.app.schemas.schemas import LocationResponse, LocationCreate
import datetime

router = APIRouter(prefix="/locations", tags=["Locations"])

@router.get("", response_model=List[LocationResponse])
def get_locations(
    location_type: Optional[str] = None,
    city: Optional[str] = None,
    active_only: bool = True,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    query = db.query(Location)
    if location_type:
        query = query.filter(Location.location_type == location_type)
    if city:
        query = query.filter(Location.city == city)
    if active_only:
        query = query.filter(Location.active_status == True)
    return query.offset(skip).limit(limit).all()

@router.get("/{location_id}", response_model=LocationResponse)
def get_location(location_id: str, db: Session = Depends(get_db)):
    loc = db.query(Location).filter(Location.location_id == location_id).first()
    if not loc:
        raise HTTPException(status_code=404, detail="Location not found")
    return loc

@router.post("", response_model=LocationResponse, status_code=201)
def create_location(loc_in: LocationCreate, db: Session = Depends(get_db)):
    count = db.query(Location).count()
    loc_id = loc_in.location_id or f"LOC-{count + 1:06d}"
    now = datetime.datetime.utcnow()
    new_loc = Location(
        location_id=loc_id,
        location_code=loc_in.location_code,
        location_name=loc_in.location_name,
        location_type=loc_in.location_type,
        parent_location_id=loc_in.parent_location_id,
        address=loc_in.address,
        city=loc_in.city,
        region=loc_in.region,
        country=loc_in.country,
        timezone=loc_in.timezone,
        active_status=loc_in.active_status,
        created_at=now
    )
    db.add(new_loc)
    db.commit()
    db.refresh(new_loc)
    return new_loc
