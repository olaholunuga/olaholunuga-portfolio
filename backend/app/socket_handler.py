"""
Socket.IO event handlers for real-time AI agent chat.
"""
from flask import current_app, request
from flask_socketio import emit, join_room, leave_room
from .cache_service import CacheService
from .extensions import socketio

# Simple in-memory cache for agent responses
cache_service = CacheService()

@socketio.on("connect")
def handle_connect():
    sid = request.sid
    join_room(sid)
    emit("connected", {"session_id": sid})

@socketio.on("chat_message")
def handle_chat_message(data):
    """
    Expected data:
    {
        "agent": "name_of_agent",
        "message": "Hello AI"
    }
    """
    sid = request.sid
    agent_name = data.get("agent", "default")
    message = data.get("message", "")

    # Try to get cached response
    cache_key = f"{agent_name}:{hash(message)}"
    cached = cache_service.get(cache_key)
    if cached:
        emit("agent_response", {"agent": agent_name, "message": cached, "cached": True}, room=sid)
        return

    # Call your existing AI agent logic here
    agents_registry = current_app.extensions.get("agents_registry", {})
    agent = agents_registry.get(agent_name)
    if not agent:
        response = f"Agent '{agent_name}' not found."
    else:
        response = agent.get_response(message)  # Adjust to your agent API

    cache_service.set(cache_key, response)
    emit("agent_response", {"agent": agent_name, "message": response, "cached": False}, room=sid)

@socketio.on("disconnect")
def handle_disconnect():
    sid = request.sid
    leave_room(sid)
