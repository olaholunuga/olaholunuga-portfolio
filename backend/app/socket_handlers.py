from flask_socketio import emit
from flask import current_app
import eventlet
import json

from .extensions import socketio

# ----------------------------
# WebSocket Event Handlers
# ----------------------------

@socketio.on("connect")
def handle_connect():
    sid = eventlet.getcurrent().greenlet.minimal_ident
    print(f"🔌 Client connected: {sid}")
    emit("connection_ack", {"message": "Connected to server."})


@socketio.on("disconnect")
def handle_disconnect():
    sid = eventlet.getcurrent().greenlet.minimal_ident
    print(f"❌ Client disconnected: {sid}")


@socketio.on("chat_message")
def handle_chat_message(data):
    """
    Expected message schema:
    {
      "agent": "career",
      "action": "assess_job_fit",
      "params": { "job_description": "..." }
    }
    """
    sid = eventlet.getcurrent().greenlet.minimal_ident
    print(f"📨 Received chat_message from {sid}: {data}")

    agent_name = data.get("agent")
    if not agent_name:
        emit("agent_error", {"error": "Missing 'agent' field in message"})
        return

    # Get agent from registry
    registry = current_app.extensions.get("agents_registry", {})
    agent = registry.get(agent_name)
    if not agent:
        emit("agent_error", {"error": f"Agent '{agent_name}' not found"})
        return

    # Start streaming task
    eventlet.spawn_n(_streaming_task, agent, data, sid)


# ----------------------------
# Background streaming
# ----------------------------
def _streaming_task(agent, message, sid):
    """
    Handles streaming agent responses back to the client.
    Always streams, even for trivial responses (hybrid mode).
    """
    try:
        emit("agent_response_start", {
            "agent": message.get("agent"),
            "action": message.get("action"),
            "request_id": message.get("request_id", "req1")
        }, to=sid)

        for chunk in agent.handle_message(message):
            # Send each chunk as it arrives
            emit("agent_response_chunk", {
                "chunk": chunk
            }, to=sid)

        emit("agent_response_end", {
            "status": "ok"
        }, to=sid)

    except Exception as e:
        emit("agent_error", {"error": f"Streaming task failed: {str(e)}"}, to=sid)