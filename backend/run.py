"""
Development entry point.
Run with: python run.py
"""
import eventlet
eventlet.monkey_patch()

# Import the app factory and the socketio instance from your package
from app import create_app, socketio

# Create the actual Flask app object
flask_app = create_app()

if __name__ == "__main__":
    socketio.run(flask_app, host="0.0.0.0", port=5000, debug=True)