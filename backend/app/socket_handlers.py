"""
WebSocket (Socket.IO) handlers for real-time chat with AI agents.

Adds *streaming* responses:
- Client sends `chat_message` with { agent, message, stream: true }
- Server emits:
    1) 'agent_response_start'  -> metadata (agent, request_id)
    2) 'agent_response_chunk'  -> multiple times with partial text chunks
    3) 'agent_response_end'    -> with final aggregated text + timings
    (on error, emits 'agent_response_error')

Also supports non-streamed replies (single 'agent_response').
"""


"""
Socket.IO event handlers for the portfolio backend.
Supports streaming and non-streaming AI agents.
Fixes 'Working outside of request context' errors by
passing socket IDs to background tasks.
"""

from flask import request
from flask_socketio import emit
from . import socketio

@socketio.on("connect")
def handle_connect():
    sid = request.sid
    print(f"🔌 Client connected: {sid}", flush=True)
    emit("server_message", {"message": "Connected to server"}, to=sid)


@socketio.on("disconnect")
def handle_disconnect():
    sid = request.sid
    print(f"❌ Client disconnected: {sid}", flush=True)


@socketio.on("chat_message")
def handle_chat_message(data):
    sid = request.sid
    print(f"📨 Received chat_message from {sid}: {data}", flush=True)

    agent_name = data.get("agent")
    message = data.get("message", "")
    stream = data.get("stream", False)

    # ✅ get the app instance while we’re in context
    app_instance = request.environ.get("flask.app")

    registry = app_instance.extensions.get("agents_registry", {})
    agent = registry.get(agent_name)
    if not agent:
        emit("agent_response_error", {"error": f"Unknown agent: {agent_name}"}, to=sid)
        return

    if stream and hasattr(agent, "stream_response"):
        socketio.start_background_task(_streaming_task, app_instance, sid, agent_name, message)
    else:
        socketio.start_background_task(_non_streaming_task, app_instance, sid, agent_name, message)


def _streaming_task(app_instance, sid, agent_name, message):
    """Runs in background — streaming."""
    print(f"🚀 Streaming task started for {agent_name} (SID: {sid})", flush=True)

    with app_instance.app_context():
        emit(
            "agent_response_start",
            {"agent": agent_name, "request_id": "req1"},
            to=sid,               # ✅ target this client
            namespace="/"         # ✅ avoid request context dependency
        )

        agent = app_instance.extensions["agents_registry"].get(agent_name)
        if not agent:
            emit(
                "agent_response_error",
                {"error": f"Unknown agent: {agent_name}"},
                to=sid,
                namespace="/"
            )
            return

        for chunk in agent.stream_response(message):
            emit(
                "agent_response_chunk",
                {"chunk": chunk},
                to=sid,
                namespace="/"
            )

        emit(
            "agent_response_end",
            {"message": "done", "duration_ms": 1000},
            to=sid,
            namespace="/"
        )

    print(f"✅ Streaming task finished for {agent_name} (SID: {sid})", flush=True)


def _non_streaming_task(app_instance, sid, agent_name, message):
    """Runs in background — non-streaming."""
    print(f"💬 Non-streaming task started for {agent_name} (SID: {sid})", flush=True)

    with app_instance.app_context():
        emit("agent_response_start", {"agent": agent_name, "request_id": "req1"}, to=sid)
        agent = app_instance.extensions["agents_registry"].get(agent_name)
        if hasattr(agent, "get_response"):
            response = agent.get_response(message)
        else:
            response = "[No response method found]"
        emit("agent_response_end", {"message": response, "duration_ms": 1000}, to=sid)

    print(f"✅ Non-streaming task finished for {agent_name} (SID: {sid})", flush=True)

