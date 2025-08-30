from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import crud, models, schemas
from ..security import get_db, get_current_active_user

router = APIRouter(
    tags=["device_stories"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=List[schemas.DeviceStory])
def read_device_stories(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    stories = crud.get_device_stories(db, skip=skip, limit=limit)
    return stories

@router.post("/", response_model=schemas.DeviceStory)
def create_device_story(
    story: schemas.DeviceStoryCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    return crud.create_device_story(db=db, story=story, user_id=current_user.id)

@router.get("/{device_story_id}/comments", response_model=List[schemas.DeviceStoryComment])
def read_comments(device_story_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    return crud.get_comments_by_device_story(db, device_story_id)

@router.post("/{device_story_id}/comments", response_model=schemas.DeviceStoryComment)
def create_comment(device_story_id: int, comment: schemas.DeviceStoryCommentCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    return crud.create_comment(db, comment, device_story_id, current_user.id)
