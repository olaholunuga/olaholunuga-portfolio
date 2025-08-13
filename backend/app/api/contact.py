# backend/app/api/contact.py
"""
Blueprint: /api/contact
Provides:
- POST /api/contact  -> submit a contact message (stored in DB)
- GET /api/contact    -> (dev/admin) list messages (later protect with auth)
"""

from flask import Blueprint, request, jsonify, current_app
from ..db import get_db
from ..models import ContactMessage
from ..rate_limit import rate_limit
from ..auth_jwt import jwt_required

bp = Blueprint("contact", __name__, url_prefix="/api/contact")

@bp.route("", methods=["POST"])
@jwt_required(role="admin")
@rate_limit()
def submit_contact():
    """
    Accept contact form submissions and store them in DB.
    Expected JSON: { name, email, subject(optional), message }
    """
    data = request.get_json() or {}
    name = data.get("name")
    email = data.get("email")
    message = data.get("message")
    if not (name and email and message):
        return jsonify({"error": "name, email and message are required"}), 400

    cm = ContactMessage(
        name=name,
        email=email,
        subject=data.get("subject"),
        message=message
    )
    with get_db() as db:
        db.add(cm)
        db.flush()
        created = cm.to_dict()

    # NOTE: later send email/notify admin here asynchronously (e.g. background job)
    return jsonify({"message": "submitted", "contact": created}), 201

@bp.route("", methods=["GET"])
@rate_limit()
def list_messages():
    """
    Dev/admin: list messages. In production protect this endpoint with auth.
    """
    with get_db() as db:
        msgs = db.query(ContactMessage).order_by(ContactMessage.created_at.desc()).all()
        payload = [m.to_dict() for m in msgs]
    return jsonify({"messages": payload})
