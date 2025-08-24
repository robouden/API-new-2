from sqlalchemy.orm import Session
import hashlib
import secrets
from . import models, schemas, security

def get_measurements(db: Session, skip: int = 0, limit: int = 1000):
    return db.query(models.Measurement).offset(skip).limit(limit).all()

def get_bgeigie_imports_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.BGeigieImport).filter(models.BGeigieImport.user_id == user_id).offset(skip).limit(limit).all()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def update_user_role(db: Session, user_id: int, role: str):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user:
        db_user.role = role
        db.commit()
        db.refresh(db_user)
    return db_user

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = security.get_password_hash(user.password)
    api_key = secrets.token_urlsafe(32)
    db_user = models.User(email=user.email, hashed_password=hashed_password, api_key=api_key)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_measurements(db: Session, measurements: list[dict], bgeigie_import_id: int):
    db_measurements = [
        models.Measurement(**measurement, bgeigie_import_id=bgeigie_import_id)
        for measurement in measurements
    ]
    db.add_all(db_measurements)
    db.commit()
    return db_measurements

def get_device_stories(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.DeviceStory).offset(skip).limit(limit).all()

def create_device_story(db: Session, story: schemas.DeviceStoryCreate, user_id: int):
    db_story = models.DeviceStory(**story.dict(), user_id=user_id)
    db.add(db_story)
    db.commit()
    db.refresh(db_story)
    return db_story

def get_devices_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Device).join(models.BGeigieImport).filter(models.BGeigieImport.user_id == user_id).offset(skip).limit(limit).all()

def create_bgeigie_import(db: Session, bgeigie_import: schemas.BGeigieImportCreate, user_id: int, file_content: bytes):
    md5sum = hashlib.md5(file_content).hexdigest()
    db_bgeigie_import = models.BGeigieImport(**bgeigie_import.dict(), user_id=user_id, md5sum=md5sum)
    db.add(db_bgeigie_import)
    db.commit()
    db.refresh(db_bgeigie_import)
    return db_bgeigie_import
