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

import time
import itertools
from typing import Iterable, Generator, Optional

from flask import current_app, request
from flask_socketio import emit, join_room, leave_room
from .cache_service import CacheService
from .extensions import socketio

try:
    # eventlet is the recommended async engine for Flask-SocketIO
    # (gevent is also fine; if you choose gevent, replace sleep calls accordingly)
    import eventlet
    eventlet.monkey_patch()  # ensure stdlib is cooperative for streaming
    sleep = eventlet.sleep
except Exception:
    # Fallback to no-op sleep if eventlet isn't available.
    # Streaming will still work, but not yield control cooperatively.
    def sleep(seconds: float = 0.0):
        return

# A small, process-wide cache to de-dup expensive agent calls
cache_service = CacheService()

# Utility to create simple unique request IDs per session
_request_counter = itertools.count(1)


def _get_agent(agent_name: str):
    """
    Fetch an agent from the app-wide registry.
    The registry is populated in create_app() and stored under `extensions`.
    """
    agents_registry = current_app.extensions.get("agents_registry", {})
    return agents_registry.get(agent_name)


def _normalize_to_stream(agent, message: str) -> Generator[str, None, None]:
    """
    Turn any agent into a *streaming* generator.

    Priority:
    1) If agent implements `stream_response(message)` -> use it directly.
    2) Else call `get_response(message)` and chunk it into word groups.
    """
    # 1) real streaming: agent provides a generator/iterator of strings
    if hasattr(agent, "stream_response") and callable(agent.stream_response):
        for chunk in agent.stream_response(message):
            # Ensure each chunk is a string (some LLM sdks yield tokens/objects)
            yield str(chunk)
        return

    # 2) fallback streaming: chunk the final string
    if hasattr(agent, "get_response") and callable(agent.get_response):
        full = str(agent.get_response(message) or "")
        # naive chunking by ~15 words per chunk for a "typing" feel
        words = full.split()
        CHUNK = 15
        for i in range(0, len(words), CHUNK):
            yield " ".join(words[i:i + CHUNK])
            sleep(0)  # yield control so packets flush smoothly
        return

    # 3) nothing to call
    yield "[agent has no stream_response/get_response implementation]"


@socketio.on("connect")
def handle_connect():
    """
    A new WebSocket client connected.
    We join a private room named by the session id so we can emit directly.
    """
    sid = request.sid
    join_room(sid)
    emit("connected", {"session_id": sid})


@socketio.on("chat_message")
def handle_chat_message(data):
    """
    Called when the client emits 'chat_message'.
    Payload example:
    {
        "agent": "welcome",
        "message": "hello there",
        "stream": true,             # optional; default False
        "cache": true,              # optional; enable/disable cache usage
        "request_id": "frontend-1"  # optional; client-generated correlation id
    }
    """
    sid = request.sid
    agent_name = (data or {}).get("agent", "default")
    message = (data or {}).get("message", "")
    want_stream = bool((data or {}).get("stream", False))
    use_cache = bool((data or {}).get("cache", True))
    client_request_id = (data or {}).get("request_id")  # your UI can set one

    # Prepare a server-side request id for tracing if client didn't pass one
    server_request_id = f"{int(time.time())}-{next(_request_counter)}"
    request_id = client_request_id or server_request_id

    # (Optional) quick cache for exact same inputs
    cache_key = f"ws:{agent_name}:{hash(message)}"
    if use_cache and not want_stream:
        cached = cache_service.get(cache_key)
        if cached:
            emit("agent_response", {
                "agent": agent_name,
                "message": cached,
                "cached": True,
                "request_id": request_id
            }, room=sid)
            return

    # Fetch the agent
    agent = _get_agent(agent_name)
    if not agent:
        emit("agent_response_error", {
            "error": f"Agent '{agent_name}' not found.",
            "request_id": request_id
        }, room=sid)
        return

    # Non-streaming path: emit once and return (compatible with your old UI)
    if not want_stream:
        try:
            # Prefer get_response; if missing, simulate via stream wrapper
            if hasattr(agent, "get_response"):
                reply = agent.get_response(message)
            else:
                reply = "".join(_normalize_to_stream(agent, message))
            if use_cache:
                cache_service.set(cache_key, reply)
            emit("agent_response", {
                "agent": agent_name,
                "message": reply,
                "cached": False,
                "request_id": request_id
            }, room=sid)
        except Exception as e:
            emit("agent_response_error", {
                "error": str(e),
                "request_id": request_id
            }, room=sid)
        return

    # Streaming path: run work in a background green thread
    def _streaming_task(room_id: str, name: str, msg: str, rid: str):
        start_ts = time.time()
        aggregated = []

        # Tell client we are starting to stream
        emit("agent_response_start", {
            "agent": name,
            "request_id": rid,
            "started_at": start_ts
        }, room=room_id)

        try:
            for chunk in _normalize_to_stream(agent, msg):
                # Append to our aggregate for the final end event
                aggregated.append(chunk)
                # Push this chunk out immediately
                emit("agent_response_chunk", {
                    "agent": name,
                    "request_id": rid,
                    "chunk": chunk
                }, room=room_id)
                # Be nice to the event loop to avoid packet coalescing
                sleep(0)

            final_text = "".join(
                c if (i == 0 or c.startswith(" ")) else f" {c}"
                for i, c in enumerate(aggregated)
            )
            duration = time.time() - start_ts

            # Send the final end signal
            emit("agent_response_end", {
                "agent": name,
                "request_id": rid,
                "message": final_text,
                "duration_ms": int(duration * 1000)
            }, room=room_id)

        except Exception as e:
            emit("agent_response_error", {
                "error": str(e),
                "agent": name,
                "request_id": rid
            }, room=room_id)

    # Kick off background streaming task
    socketio.start_background_task(_streaming_task, sid, agent_name, message, request_id)


@socketio.on("disconnect")
def handle_disconnect():
    """
    Cleanup when the client disconnects.
    """
    sid = request.sid
    leave_room(sid)