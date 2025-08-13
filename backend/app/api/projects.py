# backend/app/api/projects.py
"""
Blueprint: /api/projects
Provides:
- GET /api/projects        -> list all projects
- POST /api/projects       -> create a new project (dev usage; later protect)
"""

from flask import Blueprint, jsonify, request, current_app
from ..db import get_db
from ..rate_limit import rate_limit
from ..models import Project  # declarative model
from ..auth import auth_required
from ..auth_jwt import jwt_required

bp = Blueprint("projects", __name__, url_prefix="/api/projects")

@bp.route("", methods=["GET"])
@rate_limit()  # apply default rate limiting
def list_projects():
    """Return all projects ordered by created_at desc"""
    with get_db() as db:
        results = db.query(Project).order_by(Project.created_at.desc()).all()
        payload = [p.to_dict() for p in results]
    return jsonify({"projects": payload})

@bp.route("", methods=["POST"])
@jwt_required(role="admin")
@rate_limit()
def create_project():
    """
    Create a project.
    Expected JSON body: { title, summary(optional), description(optional), github_url(optional), live_url(optional) }
    NOTE: in production protect this endpoint (auth).
    """
    data = request.get_json() or {}
    title = data.get("title")
    if not title:
        return jsonify({"error": "title is required"}), 400

    p = Project(
        title=title,
        summary=data.get("summary"),
        description=data.get("description"),
        github_url=data.get("github_url"),
        live_url=data.get("live_url"),
    )
    with get_db() as db:
        db.add(p)
        # commit occurs automatically when context exits
        db.flush()  # ensure id is generated
        result = p.to_dict()
    return jsonify({"project": result}), 201
