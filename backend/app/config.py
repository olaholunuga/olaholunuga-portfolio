"""
Configuration module.
Loads environment variables and centralizes app settings.
"""
import os
from dotenv import load_dotenv

# Load .env file variables into environment
load_dotenv()

class Config:
    # Flask settings
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    DEBUG = os.getenv("FLASK_DEBUG", "1") == "1"

    # Database URL - defaults to SQLite
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dev.db")

    # SocketIO async mode - eventlet recommended for production
    SOCKETIO_ASYNC_MODE = os.getenv("SOCKETIO_ASYNC_MODE", "eventlet")

    # Rate limiting settings
    RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", 60))   # seconds
    RATE_LIMIT_MAX_REQUESTS = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", 120))

    # Blog API URL for proxying blog content
    BLOG_API_URL = os.getenv("BLOG_API_URL", "https://blog.olaholunuga.com/api")
