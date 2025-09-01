from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class UserBase(BaseModel):
    email: str
    name: Optional[str] = None

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

class UserProfile(BaseModel):
    name: Optional[str] = None
    email: str

class UserUpdate(BaseModel):
    role: Optional[str] = None

class BGeigieImportBase(BaseModel):
    source: str

class BGeigieImportCreate(BGeigieImportBase):
    pass

class BGeigieImport(BGeigieImportBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class BGeigieImportMetadata(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    cities: Optional[str] = None
    credits: Optional[str] = None
    subtype: Optional[str] = None

class MeasurementBase(BaseModel):
    cpm: int
    latitude: float
    longitude: float

class Measurement(MeasurementBase):
    id: int
    bgeigie_import_id: int
    device_id: Optional[int] = None
    cpm: int
    latitude: float
    longitude: float
    captured_at: datetime

    class Config:
        from_attributes = True

class DeviceBase(BaseModel):
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    sensor: Optional[str] = None
    unit: Optional[str] = None

class DeviceCreate(DeviceBase):
    pass

class Device(DeviceBase):
    id: int
    created_at: datetime
    updated_at: datetime
    measurements_count: int
    bgeigie_import_id: Optional[int] = None

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

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

class DeviceStoryCommentBase(BaseModel):
    content: str

class DeviceStoryCommentCreate(DeviceStoryCommentBase):
    pass

class DeviceStoryComment(DeviceStoryCommentBase):
    id: int
    device_story_id: int
    user_id: int

    class Config:
        from_attributes = True

User.model_rebuild()
