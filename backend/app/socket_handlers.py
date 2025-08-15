"""
Socket.IO event handlers for the portfolio backend.
Supports streaming and non-streaming AI agents.

Fixes:
- 'Working outside of request context' by avoiding flask.request in background tasks
- Properly passes Flask app instance and socket ID to threads
- Streams output even for non-streaming agents by chunking their responses
"""

from flask import request
from flask_socketio import emit
from . import socketio
import time

@socketio.on("connect")
def handle_connect():
    """Triggered when a client connects."""
    sid = request.sid
    print(f"🔌 Client connected: {sid}", flush=True)
    emit("server_message", {"message": "Connected to server"}, to=sid, namespace="/")


@socketio.on("disconnect")
def handle_disconnect():
    """Triggered when a client disconnects."""
    sid = request.sid
    print(f"❌ Client disconnected: {sid}", flush=True)


@socketio.on("chat_message")
def handle_chat_message(data):
    """
    Handle incoming chat messages from the frontend.

    Expected data:
    {
        "agent": "demo_stream",
        "message": "hello",
        "stream": true  # optional, defaults to False
    }
    """
    sid = request.sid
    print(f"📨 Received chat_message from {sid}: {data}", flush=True)

    agent_name = data.get("agent")
    message = data.get("message", "")
    stream_flag = data.get("stream", False)

    # Get app instance while in request context
    app_instance = request.environ.get("flask.app")
    registry = app_instance.extensions.get("agents_registry", {})
    agent = registry.get(agent_name)

    if not agent:
        emit(
            "agent_response_error",
            {"error": f"Unknown agent: {agent_name}"},
            to=sid,
            namespace="/"
        )
        return

    # Decide streaming mode:
    #   If explicitly requested or if agent has stream_response(), stream.
    #   Otherwise, treat as non-streaming but still send chunks.
    if stream_flag and hasattr(agent, "stream_response"):
        socketio.start_background_task(_streaming_task, app_instance, sid, agent_name, message)
    else:
        socketio.start_background_task(_non_streaming_as_stream_task, app_instance, sid, agent_name, message)


def _streaming_task(app_instance, sid, agent_name, message):
    """
    Background task for streaming agents.
    Sends agent_response_start, agent_response_chunk, and agent_response_end events.
    """
    print(f"🚀 Streaming task started for {agent_name} (SID: {sid})", flush=True)

    with app_instance.app_context():
        emit("agent_response_start", {"agent": agent_name, "request_id": "req1"}, to=sid, namespace="/")
        agent = app_instance.extensions["agents_registry"].get(agent_name)

        if not agent:
            emit("agent_response_error", {"error": f"Unknown agent: {agent_name}"}, to=sid, namespace="/")
            return

        try:
            for chunk in agent.stream_response(message):
                emit("agent_response_chunk", {"chunk": chunk}, to=sid, namespace="/")
        except Exception as e:
            emit("agent_response_error", {"error": str(e)}, to=sid, namespace="/")
            print(f"⚠️ Error in streaming agent {agent_name}: {e}", flush=True)

        emit("agent_response_end", {"message": "done", "duration_ms": 1000}, to=sid, namespace="/")

    print(f"✅ Streaming task finished for {agent_name} (SID: {sid})", flush=True)


def _non_streaming_as_stream_task(app_instance, sid, agent_name, message):
    """
    Background task for non-streaming agents.
    Sends their response in a 'chunked' style for UI consistency.
    """
    print(f"💬 Non-streaming task (as stream) started for {agent_name} (SID: {sid})", flush=True)

    with app_instance.app_context():
        emit("agent_response_start", {"agent": agent_name, "request_id": "req1"}, to=sid, namespace="/")
        agent = app_instance.extensions["agents_registry"].get(agent_name)

        if not agent:
            emit("agent_response_error", {"error": f"Unknown agent: {agent_name}"}, to=sid, namespace="/")
            return

        try:
            if hasattr(agent, "get_response"):
                response = agent.get_response(message)
            else:
                response = "[No response method found]"

            # Simulate streaming by sending in small chunks
            chunk_size = 50
            chunkk = 1
            for i in range(0, len(response), chunk_size):
                emit("agent_response_chunk", {"chunk": response[i:i+chunk_size]}, to=sid, namespace="/")
                print(F"chunk: {chunkk}")
                chunkk
                time.sleep(0.3)

        except Exception as e:
            emit("agent_response_error", {"error": str(e)}, to=sid, namespace="/")
            print(f"⚠️ Error in non-streaming agent {agent_name}: {e}", flush=True)

        emit("agent_response_end", {"message": "done", "duration_ms": 1000}, to=sid, namespace="/")

    print(f"✅ Non-streaming task finished for {agent_name} (SID: {sid})", flush=True)
