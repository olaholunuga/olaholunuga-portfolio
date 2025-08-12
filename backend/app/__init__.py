"""
App factory for portfolio backend.
"""
from flask import Flask
from .config import Config
from .extensions import socketio, create_engine_and_session, Base
from .api import blog_proxy
from . import socket_handlers  # registers event handlers

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Database setup
    engine, SessionLocal = create_engine_and_session(app.config["DATABASE_URL"])
    app.extensions = {}
    app.extensions["db_engine"] = engine
    app.extensions["db_session"] = SessionLocal

    # Register blueprints
    app.register_blueprint(blog_proxy.bp)

    # Init SocketIO
    socketio.init_app(app, async_mode=app.config["SOCKETIO_ASYNC_MODE"])

    return app
