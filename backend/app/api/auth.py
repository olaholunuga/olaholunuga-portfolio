"""
Auth endpoints:
- POST /api/auth/register  (bootstrap first admin with ADMIN_SETUP_TOKEN)
- POST /api/auth/login     (email + password -> access + refresh)
- POST /api/auth/refresh   (refresh token -> new access + refresh rotation)
- POST /api/auth/logout    (invalidate / revoke refresh token)
"""

from flask import Blueprint, request, jsonify, current_app
from ..security import hash_password, verify_password
from ..auth_jwt import generate_access_token, generate_refresh_token, verify_refresh_token, revoke_refresh_token, jwt_required
from ...app.db import get_db  # note: relative import may differ based on your tree
from ..models_user import User

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@bp.route("/register", methods=["POST"])
def register():
    """
    Register the first admin user via a one-time ADMIN_SETUP_TOKEN.
    Body: { "email": "...", "password": "...", "setup_token": "..." }
    """
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    setup_token = data.get("setup_token") or ""

    if not all([email, password, setup_token]):
        return jsonify({"error": "email, password, setup_token required"}), 400

    if setup_token != current_app.config["ADMIN_SETUP_TOKEN"]:
        return jsonify({"error": "Invalid setup token"}), 403

    with get_db() as db:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            return jsonify({"error": "User already exists"}), 400

        user = User(email=email, password_hash=hash_password(password), role="admin")
        db.add(user)
        # commit when context exits

    return jsonify({"message": "Admin registered. You can now login."}), 201


@bp.route("/login", methods=["POST"])
def login():
    """
    Login with email + password, get access & refresh tokens.
    Body: { "email": "...", "password": "..." }
    """
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    with get_db() as db:
        user = db.query(User).filter(User.email == email).first()
        if not user or not verify_password(password, user.password_hash):
            return jsonify({"error": "Invalid credentials"}), 401

        access = generate_access_token(user)
        refresh = generate_refresh_token(user, db)  # persists jti; committed on exit

        return jsonify({
            "user": user.to_safe_dict(),
            "access_token": access,
            "refresh_token": refresh
        })


@bp.route("/refresh", methods=["POST"])
def refresh():
    """
    Exchange a valid refresh token for new access + a rotated refresh token.
    Body: { "refresh_token": "..." }
    Rotation: revoke old refresh JTI, issue a new one.
    """
    data = request.get_json() or {}
    token = data.get("refresh_token") or ""
    user, jti, err = verify_refresh_token(token)
    if err:
        return jsonify({"error": err}), 401

    # revoke the old refresh token (rotation)
    revoke_refresh_token(jti)

    with get_db() as db:
        # re-fetch user to bind session for token insert
        user = db.query(User).filter(User.id == user.id).first()
        access = generate_access_token(user)
        refresh = generate_refresh_token(user, db)

    return jsonify({
        "user": user.to_safe_dict(),
        "access_token": access,
        "refresh_token": refresh
    })


@bp.route("/logout", methods=["POST"])
def logout():
    """
    Revoke a refresh token (logout).
    Body: { "refresh_token": "..." }
    """
    data = request.get_json() or {}
    token = data.get("refresh_token") or ""
    user, jti, err = verify_refresh_token(token)
    if err:
        return jsonify({"error": err}), 400

    revoke_refresh_token(jti)
    return jsonify({"message": "Logged out (refresh token revoked)."})