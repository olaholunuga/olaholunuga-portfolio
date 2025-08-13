"""
User & RefreshToken models for JWT authentication.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship
from .extensions import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(64), default="admin")  # simple roles: 'admin' (now), later 'editor', 'viewer'
    created_at = Column(DateTime, default=datetime.utcnow)

    # convenience: relationship to refresh tokens
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")

    def to_safe_dict(self):
        """Safe representation to return to clients (never include password_hash)."""
        return {
            "id": self.id,
            "email": self.email,
            "role": self.role,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    jti = Column(String(64), unique=True, nullable=False)   # JWT ID for the refresh token
    revoked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    revoked_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="refresh_tokens")

# Helpful index if you want to query fast by (user_id, revoked)
Index("ix_refresh_tokens_user_revoked", RefreshToken.user_id, RefreshToken.revoked)