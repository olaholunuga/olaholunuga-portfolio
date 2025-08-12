# backend/app/models.py
"""
Declarative SQLAlchemy models for the portfolio backend.

- Project: stores portfolio projects (all projects are shown on Projects page)
- Skill: stores skills (used by Skills & Experience)
- ContactMessage: stores messages sent via the Contact page
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.orm import relationship
# Base was created in app/extensions.py
from .extensions import Base

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    summary = Column(String(512), nullable=True)
    description = Column(Text, nullable=True)
    github_url = Column(String(1024), nullable=True)
    live_url = Column(String(1024), nullable=True)
    # created_at timestamp
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        """Serialize Project to JSON-friendly dict for API responses."""
        return {
            "id": self.id,
            "title": self.title,
            "summary": self.summary,
            "description": self.description,
            "github_url": self.github_url,
            "live_url": self.live_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    level = Column(String(64), nullable=True)  # e.g., "Intermediate", "Expert"
    category = Column(String(128), nullable=True)  # e.g., "Frontend", "Backend"
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "level": self.level,
            "category": self.category,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class ContactMessage(Base):
    __tablename__ = "contact_messages"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    subject = Column(String(255), nullable=True)
    message = Column(Text, nullable=False)
    handled = Column(Boolean, default=False)  # admin can mark as handled
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "subject": self.subject,
            "message": self.message,
            "handled": self.handled,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
