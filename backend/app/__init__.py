"""
App factory for portfolio backend.
"""
from flask import Flask
from .config import Config
from .extensions import socketio, create_engine_and_session, Base
from .api import projects_bp, skills_bp, contact_bp, blog_proxy_bp  # import blueprints
from . import socket_handlers  # ensures socket handlers are registered

def create_app(config_class=Config):
    """Create and configure the Flask application."""
    app = Flask(__name__, static_folder="../frontend/dist", template_folder="../frontend/dist")
    app.config.from_object(config_class)

    # Database setup: create engine and session factory, attach to app
    engine, SessionLocal = create_engine_and_session(app.config["DATABASE_URL"])
    app.extensions = {}
    app.extensions["db_engine"] = engine
    app.extensions["db_session"] = SessionLocal

    # Register API blueprints
    app.register_blueprint(projects_bp)
    app.register_blueprint(skills_bp)
    app.register_blueprint(contact_bp)
    app.register_blueprint(blog_proxy_bp)

    # Initialize SocketIO
    socketio.init_app(app, async_mode=app.config["SOCKETIO_ASYNC_MODE"])

    return app
