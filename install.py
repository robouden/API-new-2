import getpass
import secrets
import sys
import os
import duckdb

# Add project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from app.database import Base, SQLALCHEMY_DATABASE_URL
from app.models import User
from app.security import get_password_hash

# Use the same database URL as the main application
DATABASE_URL = "duckdb:///safecast.db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def setup_admin_user():
    """Creates the initial admin user."""
    db = SessionLocal()
    try:
        # Check if an admin user already exists
        if db.query(User).filter(User.role == 'admin').first():
            print("An admin user already exists.")
            return

        print("Creating initial admin user...")
        email = input("Enter admin email: ")
        password = getpass.getpass("Enter admin password: ")

        # Check if a user with this email already exists and update them
        user = db.query(User).filter(User.email == email).first()
        if user:
            print(f"User with email {email} already exists. Updating to admin.")
            user.role = 'admin'
        else:
            print(f"Creating new admin user with email {email}.")
            hashed_password = get_password_hash(password)
            api_key = secrets.token_urlsafe(32)
            
            # Close SQLAlchemy session and engine before opening direct DuckDB connection
            db.close()
            engine.dispose()
            
            db_path = SQLALCHEMY_DATABASE_URL.split("///")[1]
            con = duckdb.connect(database=db_path, read_only=False)
            
            # Get the next available ID
            result = con.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM users").fetchone()
            next_id = result[0]
            
            # Extract name from email (part before @)
            name = email.split('@')[0]
            
            con.execute(
                """INSERT INTO users (id, email, name, hashed_password, api_key, is_active, role)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (next_id, email, name, hashed_password, api_key, True, "admin"),
            )
            con.close()
            return  # Exit early since we already closed the db session
        
        print("Admin user created/updated successfully.")

    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    print("Initializing database...")
    # Create all tables defined in app/models.py
    create_table_statements = [
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            email VARCHAR, 
            name VARCHAR,
            hashed_password VARCHAR, 
            api_key VARCHAR, 
            is_active BOOLEAN, 
            role VARCHAR
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS bgeigie_imports (
            id INTEGER PRIMARY KEY,
            source VARCHAR,
            md5sum VARCHAR,
            user_id INTEGER REFERENCES users(id),
            status VARCHAR,
            name VARCHAR,
            description VARCHAR,
            cities VARCHAR,
            credits VARCHAR,
            subtype VARCHAR,
            measurements_count INTEGER DEFAULT 0,
            lines_count INTEGER DEFAULT 0,
            approved BOOLEAN DEFAULT FALSE,
            rejected BOOLEAN DEFAULT FALSE,
            approved_by VARCHAR,
            rejected_by VARCHAR,
            would_auto_approve BOOLEAN DEFAULT FALSE,
            auto_apprv_gps_validity BOOLEAN DEFAULT FALSE,
            auto_apprv_no_high_cpm BOOLEAN DEFAULT FALSE,
            auto_apprv_no_zero_cpm BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS measurements (
            id INTEGER PRIMARY KEY,
            cpm INTEGER,
            latitude DOUBLE,
            longitude DOUBLE,
            captured_at TIMESTAMP,
            bgeigie_import_id INTEGER REFERENCES bgeigie_imports(id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY,
            unit VARCHAR,
            sensor VARCHAR,
            bgeigie_import_id INTEGER REFERENCES bgeigie_imports(id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS device_stories (
            id INTEGER PRIMARY KEY,
            title VARCHAR,
            content VARCHAR,
            user_id INTEGER REFERENCES users(id),
            device_id INTEGER REFERENCES devices(id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS device_story_comments (
            id INTEGER PRIMARY KEY,
            content VARCHAR(1000),
            device_story_id INTEGER REFERENCES device_stories(id),
            user_id INTEGER REFERENCES users(id),
            image_path VARCHAR
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS bgeigie_logs (
            id INTEGER PRIMARY KEY,
            cpm INTEGER,
            latitude DOUBLE,
            longitude DOUBLE,
            computed_location VARCHAR,
            bgeigie_import_id INTEGER REFERENCES bgeigie_imports(id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS maps (
            id INTEGER PRIMARY KEY
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS measurement_imports (
            id INTEGER PRIMARY KEY,
            source VARCHAR,
            md5sum VARCHAR,
            status VARCHAR,
            subtype VARCHAR,
            map_id INTEGER REFERENCES maps(id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS measurement_import_logs (
            id INTEGER PRIMARY KEY,
            measurement_import_id INTEGER REFERENCES measurement_imports(id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS drive_imports (
            id INTEGER PRIMARY KEY,
            source VARCHAR,
            md5sum VARCHAR,
            status VARCHAR
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS drive_logs (
            id INTEGER PRIMARY KEY,
            drive_import_id INTEGER REFERENCES drive_imports(id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS ingest_measurements (
            id INTEGER PRIMARY KEY,
            cpm INTEGER,
            latitude DOUBLE,
            longitude DOUBLE
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS uploader_contact_histories (
            id INTEGER PRIMARY KEY,
            user_id INTEGER REFERENCES users(id)
        );
        """
    ]

    with engine.connect() as connection:
        for statement in create_table_statements:
            connection.execute(text(statement))
        connection.commit()
    print("Database initialized.")
    
    setup_admin_user()

    # Dispose of the engine to release the connection
    engine.dispose()
