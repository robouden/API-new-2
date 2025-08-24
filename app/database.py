from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base

SQLALCHEMY_DATABASE_URL = "duckdb:///safecast.duckdb"

Base = declarative_base()

def setup_database(engine):
    Base.metadata.create_all(bind=engine)
