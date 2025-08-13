"""
Configuration module.
Loads environment variables and centralizes app settings.
"""
import os
from dotenv import load_dotenv

# Load .env file variables into environment
load_dotenv()

class Config:
    # ... existing settings (DATABASE_URL, SOCKETIO_ASYNC_MODE, etc.)
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")  # used by Flask, sessions, etc.

    # JWT settings
    JWT_SECRET = os.getenv("JWT_SECRET", "dev-jwt-secret-change-me")  # signing key for JWT
    JWT_ALG = os.getenv("JWT_ALG", "HS256")                           # signing algorithm
    JWT_ACCESS_TTL = int(os.getenv("JWT_ACCESS_TTL", "900"))          # 15 minutes (in seconds)
    JWT_REFRESH_TTL = int(os.getenv("JWT_REFRESH_TTL", "2592000"))    # 30 days (in seconds)

    # Admin bootstrap token — used to allow first /register call
    ADMIN_SETUP_TOKEN = os.getenv("ADMIN_SETUP_TOKEN", "")            # set a strong one in .env for initial admin

    # (Optional) CORS aware domains for auth if you enable CORS later
    FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

    # Flask settings
    # SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
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
