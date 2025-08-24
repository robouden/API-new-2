from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .database import setup_database, SQLALCHEMY_DATABASE_URL
from .routers import users, bgeigie_imports, measurements, devices, device_stories

load_dotenv()  # Load environment variables from .env file

app = FastAPI()

@app.on_event("startup")
def on_startup():
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    app.state.db_engine = engine
    app.state.db_sessionmaker = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    setup_database(engine)

app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(bgeigie_imports.router, prefix="/bgeigie_imports", tags=["bgeigie_imports"])
app.include_router(measurements.router, prefix='/measurements', tags=['measurements'])
app.include_router(devices.router, prefix='/devices', tags=['devices'])
app.include_router(device_stories.router, prefix='/device_stories', tags=['device_stories'])

app.mount("/static", StaticFiles(directory=str(Path(__file__).parent / "static")), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open(Path(__file__).parent / "templates/index.html") as f:
        return HTMLResponse(content=f.read(), status_code=200)
