from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

SQLALCHEMY_DATABASE_URL = "duckdb:///safecast.db"

Base = declarative_base()

# Create SessionLocal for background tasks
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def setup_database(engine):
    Base.metadata.create_all(bind=engine)
