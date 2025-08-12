"""
Database helpers for getting sessions.
Ensures sessions are committed/rolled back properly.
"""
from contextlib import contextmanager
from flask import current_app

@contextmanager
def get_db():
    """
    Context manager to handle database sessions.
    Usage:
        with get_db() as db:
            db.query(...)
    """
    SessionLocal = current_app.extensions["db_session"]
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
        SessionLocal.remove()