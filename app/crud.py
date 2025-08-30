from sqlalchemy.orm import Session
from sqlalchemy import text
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
    
    # Get next available ID
    result = db.execute(text("SELECT COALESCE(MAX(id), 0) + 1 FROM users")).fetchone()
    next_id = result[0]
    
    db_user = models.User(id=next_id, email=user.email, hashed_password=hashed_password, api_key=api_key)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_measurements(db: Session, measurements: list[dict], bgeigie_import_id: int):
    # Get next available ID
    result = db.execute(text("SELECT COALESCE(MAX(id), 0) FROM measurements")).fetchone()
    start_id = result[0] + 1 if result[0] else 1
    
    db_measurements = []
    for i, measurement in enumerate(measurements):
        db_measurement = models.Measurement(id=start_id + i, **measurement, bgeigie_import_id=bgeigie_import_id)
        db_measurements.append(db_measurement)
    
    db.add_all(db_measurements)
    db.commit()
    return db_measurements

def get_device_stories(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.DeviceStory).offset(skip).limit(limit).all()

def create_device_story(db: Session, story: schemas.DeviceStoryCreate, user_id: int):
    # Get next available ID
    result = db.execute(text("SELECT COALESCE(MAX(id), 0) + 1 FROM device_stories")).fetchone()
    next_id = result[0]
    
    db_story = models.DeviceStory(id=next_id, **story.dict(), user_id=user_id)
    db.add(db_story)
    db.commit()
    db.refresh(db_story)
    return db_story

def get_devices_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Device).join(models.BGeigieImport).filter(models.BGeigieImport.user_id == user_id).offset(skip).limit(limit).all()

def create_bgeigie_import(db: Session, bgeigie_import: schemas.BGeigieImportCreate, user_id: int, file_content: bytes):
    md5sum = hashlib.md5(file_content).hexdigest()
    
    # Get next available ID
    result = db.execute(text("SELECT COALESCE(MAX(id), 0) + 1 FROM bgeigie_imports")).fetchone()
    next_id = result[0]
    
    db_bgeigie_import = models.BGeigieImport(id=next_id, **bgeigie_import.dict(), user_id=user_id, md5sum=md5sum)
    db.add(db_bgeigie_import)
    db.commit()
    db.refresh(db_bgeigie_import)
    return db_bgeigie_import

def get_measurements_count(db: Session):
    return db.query(models.Measurement).count()

def get_comments_by_device_story(db: Session, device_story_id: int):
    return db.query(models.DeviceStoryComment).filter(models.DeviceStoryComment.device_story_id == device_story_id).all()

def create_comment(db: Session, comment: schemas.DeviceStoryCommentCreate, device_story_id: int, user_id: int):
    # Get next available ID
    result = db.execute(text("SELECT COALESCE(MAX(id), 0) + 1 FROM device_story_comments")).fetchone()
    next_id = result[0]
    
    db_comment = models.DeviceStoryComment(id=next_id, **comment.dict(), device_story_id=device_story_id, user_id=user_id)
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment

def update_bgeigie_import_status(db: Session, import_id: int, status: str, user_id: int = None):
    query = db.query(models.BGeigieImport).filter(models.BGeigieImport.id == import_id)
    if user_id:
        query = query.filter(models.BGeigieImport.user_id == user_id)
    db_import = query.first()
    if db_import:
        db_import.status = status
        db.commit()
        db.refresh(db_import)
    return db_import
