from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import crud, schemas, models
from ..security import get_db, get_current_active_user

router = APIRouter(
    tags=["measurements"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=List[schemas.Measurement])
def read_measurements(
    skip: int = 0,
    limit: int = 1000,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    measurements = crud.get_measurements(db, skip=skip, limit=limit)
    return measurements
