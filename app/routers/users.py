from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from .. import crud, models, schemas, email
from ..security import (
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    get_current_active_user,
    get_current_admin_user,
    get_current_moderator_user,
    get_db,
    verify_password,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)

router = APIRouter()

@router.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = crud.create_user(db=db, user=user)
    background_tasks.add_task(email.send_signup_confirmation, email_to=new_user.email, user=new_user)
    return new_user

@router.put("/{user_id}/role", response_model=schemas.User)
def set_user_role(
    user_id: int,
    user_update: schemas.UserUpdate,
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(get_current_admin_user)
):
    if user_update.role not in ["user", "moderator", "admin"]:
        raise HTTPException(status_code=400, detail="Invalid role specified.")
    
    updated_user = crud.update_user_role(db=db, user_id=user_id, role=user_update.role)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found.")
    return updated_user

@router.get("/users/all", response_model=List[schemas.User])
def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users

@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, email=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"sub": user.email})
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@router.post("/refresh", response_model=schemas.Token)
async def refresh_access_token(refresh_request: schemas.RefreshTokenRequest, db: Session = Depends(get_db)):
    email = verify_refresh_token(refresh_request.refresh_token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = crud.get_user_by_email(db, email=email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"sub": user.email})
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@router.get("/users/me", response_model=schemas.User)
async def read_users_me(current_user: models.User = Depends(get_current_active_user)):
    return current_user

@router.get("/users/me/items/")
async def read_own_items(current_user: models.User = Depends(get_current_active_user)):
    return [{"item_id": "Foo", "owner": current_user.email}]

@router.get("/admin/", tags=["admin"])
async def admin_panel(current_user: models.User = Depends(get_current_admin_user)):
    return {"message": f"Welcome, admin {current_user.email}!"}

@router.get("/moderator/", tags=["moderator"])
async def moderator_panel(current_user: models.User = Depends(get_current_moderator_user)):
    return {"message": f"Welcome, moderator {current_user.email}!"}
