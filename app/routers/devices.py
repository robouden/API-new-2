from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import crud, models, schemas
from ..security import get_db, get_current_active_user

router = APIRouter(
    tags=["devices"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=List[schemas.Device])
def read_devices(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Retrieve devices for the current user.
    """
    devices = crud.get_devices_by_user(db, user_id=current_user.id, skip=skip, limit=limit)
    return devices
