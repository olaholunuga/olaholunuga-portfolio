"""
App extensions setup:
- SQLAlchemy Engine + session
- Socket.IO
- Declarative base for models
"""
import os
from flask_socketio import SocketIO
from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker, declarative_base

# Create declarative base for SQLAlchemy models
Base = declarative_base()

# SocketIO instance (initialized later in app factory)
socketio = SocketIO(cors_allowed_origins="*")

def create_engine_and_session(database_url: str):
    """
    Creates SQLAlchemy engine and session factory.
    For SQLite, uses check_same_thread=False and small pool size.
    """
    connect_args = {}
    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    engine = create_engine(
        database_url,
        pool_size=int(os.getenv("DB_POOL_SIZE", 5)),
        max_overflow=int(os.getenv("DB_MAX_OVERFLOW", 10)),
        pool_pre_ping=True,
        future=True,
        connect_args=connect_args
    )

    # scoped_session ensures thread safety in Flask
    SessionLocal = scoped_session(
        sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    )

    return engine, SessionLocal
