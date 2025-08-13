# backend/app/api/__init__.py
"""
Central place to import API blueprints for registration by the app factory.
"""
from .projects import bp as projects_bp
from .skills import bp as skills_bp
from .contact import bp as contact_bp
from .blog_proxy import bp as blog_proxy_bp
from .auth import bp as auth_bp
from .agents import bp as agents_bp

__all__ = ["projects_bp", "skills_bp", "contact_bp", "blog_proxy_bp", "auth_bp", "agents_bp"]
