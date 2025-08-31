from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Float, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    api_key = Column(String, unique=True, index=True)
    is_active = Column(Boolean, default=True)
    role = Column(String, default="user")  # Roles: user, moderator, admin

    bgeigie_imports = relationship("BGeigieImport", back_populates="user")
    device_stories = relationship("DeviceStory", back_populates="owner")
    comments = relationship("DeviceStoryComment", back_populates="user")

class BGeigieImport(Base):
    __tablename__ = "bgeigie_imports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String)
    md5sum = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String, default="unprocessed")
    name = Column(String)
    description = Column(String)
    cities = Column(String)
    credits = Column(String)
    subtype = Column(String)
    measurements_count = Column(Integer, default=0)
    lines_count = Column(Integer, default=0)
    approved = Column(Boolean, default=False)
    rejected = Column(Boolean, default=False)
    approved_by = Column(String)
    rejected_by = Column(String)
    would_auto_approve = Column(Boolean, default=False)
    auto_apprv_gps_validity = Column(Boolean, default=False)
    auto_apprv_no_high_cpm = Column(Boolean, default=False)
    auto_apprv_no_zero_cpm = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="bgeigie_imports")
    measurements = relationship("Measurement", back_populates="bgeigie_import")
    devices = relationship("Device", back_populates="bgeigie_import")
    logs = relationship("BGeigieLog", back_populates="bgeigie_import")

class Measurement(Base):
    __tablename__ = "measurements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cpm = Column(Integer)
    latitude = Column(Float)
    longitude = Column(Float)
    captured_at = Column(DateTime)
    bgeigie_import_id = Column(Integer, ForeignKey("bgeigie_imports.id"))

    bgeigie_import = relationship("BGeigieImport", back_populates="measurements")

class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    unit = Column(String)
    sensor = Column(String)
    bgeigie_import_id = Column(Integer, ForeignKey("bgeigie_imports.id"), nullable=True)

    bgeigie_import = relationship("BGeigieImport", back_populates="devices")
    device_stories = relationship("DeviceStory", back_populates="device")

class DeviceStory(Base):
    __tablename__ = "device_stories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, index=True)
    content = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))
    device_id = Column(Integer, ForeignKey("devices.id"))

    owner = relationship("User", back_populates="device_stories")
    device = relationship("Device", back_populates="device_stories")
    comments = relationship("DeviceStoryComment", back_populates="device_story")

class DeviceStoryComment(Base):
    __tablename__ = "device_story_comments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    content = Column(String(1000))
    device_story_id = Column(Integer, ForeignKey("device_stories.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    image_path = Column(String, nullable=True)

    device_story = relationship("DeviceStory", back_populates="comments")
    user = relationship("User", back_populates="comments")

class BGeigieLog(Base):
    __tablename__ = "bgeigie_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cpm = Column(Integer)
    latitude = Column(Float)
    longitude = Column(Float)
    computed_location = Column(String)
    bgeigie_import_id = Column(Integer, ForeignKey("bgeigie_imports.id"))

    bgeigie_import = relationship("BGeigieImport", back_populates="logs")

class Map(Base):
    __tablename__ = "maps"

    id = Column(Integer, primary_key=True, autoincrement=True)

    measurement_imports = relationship("MeasurementImport", back_populates="map")

class MeasurementImport(Base):
    __tablename__ = "measurement_imports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String)
    md5sum = Column(String)
    status = Column(String, default="unprocessed")
    subtype = Column(String, default="None")
    map_id = Column(Integer, ForeignKey("maps.id"))

    map = relationship("Map", back_populates="measurement_imports")
    logs = relationship("MeasurementImportLog", back_populates="measurement_import")

class MeasurementImportLog(Base):
    __tablename__ = "measurement_import_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    measurement_import_id = Column(Integer, ForeignKey("measurement_imports.id"))

    measurement_import = relationship("MeasurementImport", back_populates="logs")

class DriveImport(Base):
    __tablename__ = "drive_imports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String)
    md5sum = Column(String)
    status = Column(String, default="unprocessed")

class DriveLog(Base):
    __tablename__ = "drive_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    drive_import_id = Column(Integer, ForeignKey("drive_imports.id"))

class IngestMeasurement(Base):
    __tablename__ = "ingest_measurements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cpm = Column(Integer)
    latitude = Column(Float)
    longitude = Column(Float)

class UploaderContactHistory(Base):
    __tablename__ = "uploader_contact_histories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
