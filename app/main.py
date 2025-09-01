from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqladmin import Admin, ModelView
from contextlib import asynccontextmanager
from .database import setup_database, SQLALCHEMY_DATABASE_URL
from .routers import users, bgeigie_imports, measurements, devices, device_stories
from .background_tasks import start_background_processor, stop_background_processor
from . import models

load_dotenv()  # Load environment variables from .env file

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    app.state.db_engine = engine
    app.state.db_sessionmaker = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    setup_database(engine)

    # Setup admin interface
    admin = Admin(app, engine)
    admin.add_view(UserAdmin)
    admin.add_view(BGeigieImportAdmin)
    admin.add_view(MeasurementAdmin)
    admin.add_view(DeviceAdmin)
    admin.add_view(DeviceStoryAdmin)
    admin.add_view(DeviceStoryCommentAdmin)
    admin.add_view(BGeigieLogAdmin)

    await start_background_processor()
    
    yield
    
    # Shutdown logic
    await stop_background_processor()

app = FastAPI(lifespan=lifespan)

class UserAdmin(ModelView, model=models.User):
    column_list = [models.User.id, models.User.email, models.User.role, models.User.is_active]

class BGeigieImportAdmin(ModelView, model=models.BGeigieImport):
    column_list = [models.BGeigieImport.id, models.BGeigieImport.source, models.BGeigieImport.status]

class MeasurementAdmin(ModelView, model=models.Measurement):
    column_list = [models.Measurement.id, models.Measurement.cpm, models.Measurement.latitude, models.Measurement.longitude]

class DeviceAdmin(ModelView, model=models.Device):
    column_list = [models.Device.id, models.Device.unit, models.Device.sensor, models.Device.bgeigie_import_id]

class DeviceStoryAdmin(ModelView, model=models.DeviceStory):
    column_list = [models.DeviceStory.id, models.DeviceStory.title]

class DeviceStoryCommentAdmin(ModelView, model=models.DeviceStoryComment):
    column_list = [models.DeviceStoryComment.id, models.DeviceStoryComment.content]

class BGeigieLogAdmin(ModelView, model=models.BGeigieLog):
    column_list = [models.BGeigieLog.id, models.BGeigieLog.cpm, models.BGeigieLog.latitude, models.BGeigieLog.longitude]


app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(bgeigie_imports.router, prefix="/bgeigie-imports", tags=["bgeigie_imports"])
app.include_router(measurements.router, prefix='/measurements', tags=['measurements'])
app.include_router(devices.router, prefix='/devices', tags=['devices'])
app.include_router(device_stories.router, prefix='/device_stories', tags=['device_stories'])

app.mount("/static", StaticFiles(directory=str(Path(__file__).parent / "static")), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open(Path(__file__).parent / "templates/index.html") as f:
        return HTMLResponse(content=f.read(), status_code=200)
