import getpass
import secrets
import sys
import os

# Add project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import User
from app.security import get_password_hash

# Use the same database URL as the main application
DATABASE_URL = "duckdb:///safecast.duckdb"

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
            user = User(
                email=email,
                hashed_password=hashed_password,
                api_key=api_key,
                role='admin',
                is_active=True
            )
            db.add(user)
        
        db.commit()
        print("Admin user created/updated successfully.")

    finally:
        db.close()

if __name__ == "__main__":
    print("Initializing database...")
    # Create all tables defined in app/models.py
    Base.metadata.create_all(bind=engine)
    print("Database initialized.")
    
    setup_admin_user()

    # Dispose of the engine to release the connection
    engine.dispose()
