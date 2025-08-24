import getpass
import secrets
import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add app directory to path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'app')))

from database import Base
from models import User
from security import get_password_hash

DATABASE_URL = "duckdb:///./safecast.db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def setup_admin_user():
    db = SessionLocal()
    try:
        # Check if an admin user already exists
        admin_user = db.query(User).filter(User.role == 'admin').first()
        if admin_user:
            print("An admin user already exists.")
            return

        print("Creating initial admin user...")
        email = input("Enter admin email: ")
        password = getpass.getpass("Enter admin password: ")

        # Check if user with this email already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            print(f"User with email {email} already exists. Updating to admin.")
            existing_user.role = 'admin'
        else:
            print(f"Creating new admin user with email {email}.")
            hashed_password = get_password_hash(password)
            api_key = secrets.token_urlsafe(32)
            new_user = User(
                email=email, 
                hashed_password=hashed_password, 
                api_key=api_key,
                role='admin', 
                is_active=True
            )
            db.add(new_user)
        
        db.commit()
        print("Admin user created/updated successfully.")

    finally:
        db.close()

if __name__ == "__main__":
    # Create all tables
    print("Initializing database...")
    Base.metadata.create_all(bind=engine)
    print("Database initialized.")
    
    setup_admin_user()
