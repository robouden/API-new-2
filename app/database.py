from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

SQLALCHEMY_DATABASE_URL = "duckdb:///safecast.db"

Base = declarative_base()

def setup_database(engine):
    Base.metadata.create_all(bind=engine)
