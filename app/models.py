from sqlalchemy import Boolean, Column, Integer, String, Float, DateTime, ForeignKey, Sequence
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, Sequence("user_id_seq"), primary_key=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    api_key = Column(String, unique=True, index=True)
    is_active = Column(Boolean, default=True)
    role = Column(String, default="user")  # Roles: user, moderator, admin

    bgeigie_imports = relationship("BGeigieImport", back_populates="owner")
    device_stories = relationship("DeviceStory", back_populates="owner")

class BGeigieImport(Base):
    __tablename__ = "bgeigie_imports"

    id = Column(Integer, Sequence("bgeigie_import_id_seq"), primary_key=True)
    source = Column(String)
    md5sum = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="bgeigie_imports")
    measurements = relationship("Measurement", back_populates="bgeigie_import")
    devices = relationship("Device", back_populates="bgeigie_import")

class Measurement(Base):
    __tablename__ = "measurements"

    id = Column(Integer, Sequence("measurement_id_seq"), primary_key=True)
    cpm = Column(Integer)
    latitude = Column(Float)
    longitude = Column(Float)
    captured_at = Column(DateTime)
    bgeigie_import_id = Column(Integer, ForeignKey("bgeigie_imports.id"))

    bgeigie_import = relationship("BGeigieImport", back_populates="measurements")

class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, Sequence("device_id_seq"), primary_key=True)
    unit = Column(String)
    sensor = Column(String)
    bgeigie_import_id = Column(Integer, ForeignKey("bgeigie_imports.id"))

    bgeigie_import = relationship("BGeigieImport", back_populates="devices")
    device_stories = relationship("DeviceStory", back_populates="device")

class DeviceStory(Base):
    __tablename__ = "device_stories"

    id = Column(Integer, Sequence("device_story_id_seq"), primary_key=True)
    title = Column(String, index=True)
    content = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))
    device_id = Column(Integer, ForeignKey("devices.id"))

    owner = relationship("User", back_populates="device_stories")
    device = relationship("Device", back_populates="device_stories")
