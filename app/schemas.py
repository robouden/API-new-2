from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class UserBase(BaseModel):
    email: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    api_key: str
    is_active: bool
    role: str
    bgeigie_imports: List['BGeigieImport'] = []
    device_stories: List['DeviceStory'] = []

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    role: Optional[str] = None

class BGeigieImportBase(BaseModel):
    source: str

class BGeigieImportCreate(BGeigieImportBase):
    pass

class BGeigieImport(BGeigieImportBase):
    id: int
    user_id: int
    md5sum: str

    class Config:
        from_attributes = True

class MeasurementBase(BaseModel):
    cpm: int
    latitude: float
    longitude: float

class Measurement(MeasurementBase):
    id: int
    bgeigie_import_id: int
    cpm: int
    latitude: float
    longitude: float
    captured_at: datetime

    class Config:
        from_attributes = True

class Device(BaseModel):
    id: int
    bgeigie_import_id: int
    unit: str
    sensor: str

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class DeviceStoryBase(BaseModel):
    title: str
    content: str

class DeviceStoryCreate(DeviceStoryBase):
    device_id: int

class DeviceStory(DeviceStoryBase):
    id: int
    user_id: int
    device_id: int

    class Config:
        from_attributes = True

User.model_rebuild()
