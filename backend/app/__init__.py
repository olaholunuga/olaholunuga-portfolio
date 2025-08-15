"""
App factory for portfolio backend.
"""
from flask import Flask
from .config import Config
from .extensions import socketio, create_engine_and_session, Base
from .api import projects_bp, skills_bp, contact_bp, blog_proxy_bp, auth_bp, agents_bp
from .agents.welcomeagent import WelcomeAgent
from .agents.projectagent import ProjectAgent
from .agents.careeragent import CareerAgent
from .agents.clientagent import ClientAgent
from .agents.researchagent import ResearchAgent
from .agents.demo_stream_agent import DemoStreamAgent

def create_app(config_class=Config):
    app = Flask(__name__, static_folder="../frontend/dist", template_folder="../frontend/dist")
    app.config.from_object(config_class)

    # Database setup
    engine, SessionLocal = create_engine_and_session(app.config["DATABASE_URL"])
    app.extensions = {}
    app.extensions["db_engine"] = engine
    app.extensions["db_session"] = SessionLocal

    # Create agent instances and store in registry
    app.extensions["agents_registry"] = {
        "welcome": WelcomeAgent(),
        "project": ProjectAgent(),
        "career": CareerAgent(),
        "client": ClientAgent(),
        "research": ResearchAgent(),
        "demo_stream": DemoStreamAgent(),  
    }

    # Register blueprints
    app.register_blueprint(agents_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(skills_bp)
    app.register_blueprint(contact_bp)
    app.register_blueprint(blog_proxy_bp)

    # Initialize SocketIO
    socketio.init_app(app, async_mode=app.config["SOCKETIO_ASYNC_MODE"])

    # Import socket handlers *after* socketio is ready to avoid circular import
    from . import socket_handlers  # noqa: E402

    return app
