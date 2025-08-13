# backend/app/api/skills.py
"""
Blueprint: /api/skills
Provides:
- GET /api/skills        -> list all skills
- POST /api/skills       -> add a skill
"""

from flask import Blueprint, jsonify, request
from ..rate_limit import rate_limit
from ..db import get_db
from ..models import Skill
from ..auth_jwt import jwt_required

bp = Blueprint("skills", __name__, url_prefix="/api/skills")

@bp.route("", methods=["GET"])
@rate_limit()
def list_skills():
    """Return skills grouped (simple list for now)."""
    with get_db() as db:
        skills = db.query(Skill).order_by(Skill.name.asc()).all()
        payload = [s.to_dict() for s in skills]
    return jsonify({"skills": payload})

@bp.route("", methods=["POST"])
@jwt_required(role="admin")
@rate_limit()
def add_skill():
    """
    Add a new skill.
    Expected JSON: { name, level(optional), category(optional) }
    """
    data = request.get_json() or {}
    name = data.get("name")
    if not name:
        return jsonify({"error": "name is required"}), 400

    skill = Skill(name=name, level=data.get("level"), category=data.get("category"))
    with get_db() as db:
        db.add(skill)
        db.flush()
        result = skill.to_dict()
    return jsonify({"skill": result}), 201
