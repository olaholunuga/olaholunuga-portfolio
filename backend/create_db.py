# backend/create_db.py
"""
Helper script to create database tables and optionally seed sample data.
Run: python create_db.py
"""

from app import create_app
from app.extensions import Base
from app.models import Project, Skill, ContactMessage
from app.extensions import create_engine_and_session
from app.config import Config
import os

def main():
    app = create_app(Config)
    engine = app.extensions["db_engine"]

    # Create all tables (if they don't exist)
    Base.metadata.create_all(bind=engine)
    print("Created (or verified) all tables.")

if __name__ == "__main__":
    main()
