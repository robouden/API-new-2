from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from .. import crud, models, schemas
from ..security import get_db, get_current_active_user

router = APIRouter(
    tags=["devices"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=List[schemas.Device])
def read_devices(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    order: Optional[str] = Query(None, description="Order by field (id, manufacturer, model, sensor, measurements_count)"),
    db: Session = Depends(get_db)
):
    """
    Retrieve all devices with optional filtering and ordering.
    """
    query = db.query(models.Device)
    
    # Apply ordering
    if order:
        if order.endswith(" desc"):
            field = order.replace(" desc", "")
            if hasattr(models.Device, field):
                query = query.order_by(desc(getattr(models.Device, field)))
        elif order.endswith(" asc"):
            field = order.replace(" asc", "")
            if hasattr(models.Device, field):
                query = query.order_by(asc(getattr(models.Device, field)))
        else:
            if hasattr(models.Device, order):
                query = query.order_by(asc(getattr(models.Device, order)))
    
    devices = query.offset(skip).limit(limit).all()
    return devices

@router.post("/", response_model=schemas.Device)
def create_device(
    device: schemas.DeviceCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Create a new device.
    """
    return crud.create_device(db=db, device=device)

@router.get("/{device_id}", response_model=schemas.Device)
def read_device(
    device_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific device by ID.
    """
    device = crud.get_device(db, device_id=device_id)
    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")
    return device

@router.put("/{device_id}", response_model=schemas.Device)
def update_device(
    device_id: int,
    device_update: schemas.DeviceCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Update a device.
    """
    device = crud.get_device(db, device_id=device_id)
    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")
    
    return crud.update_device(db=db, device_id=device_id, device_update=device_update)

@router.delete("/{device_id}")
def delete_device(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Delete a device.
    """
    device = crud.get_device(db, device_id=device_id)
    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")
    
    crud.delete_device(db=db, device_id=device_id)
    return {"message": "Device deleted successfully"}
