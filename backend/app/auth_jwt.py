"""
JWT helpers & decorators for:
- generating access and refresh tokens
- verifying tokens & roles
- refreshing and revoking refresh tokens
"""

import time
import uuid
import jwt
from functools import wraps
from typing import Optional, Tuple
from flask import request, current_app, jsonify, g
from sqlalchemy.orm import Session
from .models_user import User, RefreshToken
from .db import get_db

# ---- Token generation ---------------------------------------------------------

def _now() -> int:
    """Return current UTC epoch seconds."""
    return int(time.time())

def _encode(payload: dict) -> str:
    """Sign a JWT with configured secret & algorithm."""
    return jwt.encode(
        payload,
        current_app.config["JWT_SECRET"],
        algorithm=current_app.config["JWT_ALG"]
    )

def _decode(token: str) -> dict:
    """Verify and decode a JWT, raising on failure."""
    return jwt.decode(
        token,
        current_app.config["JWT_SECRET"],
        algorithms=[current_app.config["JWT_ALG"]],
        options={"require": ["exp", "iat", "nbf", "jti", "sub", "typ"]}  # stricter claims
    )

def generate_access_token(user: User) -> str:
    """
    Short-lived access token: used on most API requests in Authorization header.
    """
    now = _now()
    payload = {
        "iss": "olaholunuga-portfolio",               # issuer
        "sub": str(user.id),                           # subject: user id (string)
        "typ": "access",                               # token type
        "iat": now,                                    # issued at
        "nbf": now,                                    # not before
        "exp": now + current_app.config["JWT_ACCESS_TTL"], # expiry seconds
        "jti": uuid.uuid4().hex,                       # unique token id
        "role": user.role,                              # include role for quick checks
        "email": user.email,                            # optional convenience
    }
    return _encode(payload)

def generate_refresh_token(user: User, db: Session) -> str:
    """
    Long-lived refresh token (rotatable). We store the token JTI in DB for revocation.
    """
    now = _now()
    jti = uuid.uuid4().hex
    payload = {
        "iss": "olaholunuga-portfolio",
        "sub": str(user.id),
        "typ": "refresh",
        "iat": now,
        "nbf": now,
        "exp": now + current_app.config["JWT_REFRESH_TTL"],
        "jti": jti
    }
    token = _encode(payload)
    # persist jti to allow revocation
    db_token = RefreshToken(user_id=user.id, jti=jti, revoked=False)
    db.add(db_token)
    # commit happens in route's DB context
    return token

# ---- Decorators & helpers -----------------------------------------------------

def _get_auth_header_token() -> Optional[str]:
    """
    Extract Bearer token from Authorization header.
    """
    auth = request.headers.get("Authorization", "")
    parts = auth.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    return None

def current_user() -> Optional[User]:
    """
    Lazy-load current user from g (set by jwt_required).
    """
    return getattr(g, "current_user", None)

def jwt_required(role: Optional[str] = None):
    """
    Decorator to protect endpoints with a valid *access* token.
    Optionally enforce role: @jwt_required(role="admin")
    """
    def wrapper(fn):
        @wraps(fn)
        def inner(*args, **kwargs):
            token = _get_auth_header_token()
            if not token:
                return jsonify({"error": "Missing Authorization Bearer token"}), 401
            try:
                data = _decode(token)
            except jwt.ExpiredSignatureError:
                return jsonify({"error": "Access token expired"}), 401
            except jwt.InvalidTokenError as e:
                return jsonify({"error": f"Invalid token: {str(e)}"}), 401

            # ensure this is an access token
            if data.get("typ") != "access":
                return jsonify({"error": "Wrong token type"}), 401

            # load user
            user_id = int(data.get("sub", "0"))
            with get_db() as db:
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    return jsonify({"error": "User not found"}), 401
                # attach user to request context
                g.current_user = user

            # optional role enforcement
            if role and user.role != role:
                return jsonify({"error": "Insufficient role"}), 403

            return fn(*args, **kwargs)
        return inner
    return wrapper

# Helper to validate refresh tokens (and return User + jti)
def verify_refresh_token(token: str) -> Tuple[Optional[User], Optional[str], Optional[str]]:
    """
    Verify refresh token and check DB for revocation.
    Returns (user, jti, error_message).
    """
    try:
        data = _decode(token)
    except jwt.ExpiredSignatureError:
        return None, None, "Refresh token expired"
    except jwt.InvalidTokenError as e:
        return None, None, f"Invalid refresh token: {str(e)}"

    if data.get("typ") != "refresh":
        return None, None, "Wrong token type"

    user_id = int(data.get("sub", "0"))
    jti = data.get("jti")
    with get_db() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None, None, "User not found"

        rt = db.query(RefreshToken).filter(RefreshToken.jti == jti).first()
        if not rt or rt.revoked:
            return None, None, "Refresh token is revoked or unknown"
    return user, jti, None

def revoke_refresh_token(jti: str) -> None:
    """Mark a refresh token as revoked in DB."""
    with get_db() as db:
        rt = db.query(RefreshToken).filter(RefreshToken.jti == jti).first()
        if rt and not rt.revoked:
            rt.revoked = True
            rt.revoked_at = __import__("datetime").datetime.utcnow()