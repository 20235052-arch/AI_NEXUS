"""
In-memory chat history store, keyed by session_id.

Good enough for a hackathon demo running a single backend process.
Swap this module for Redis (or a DB table) before any real deployment —
an in-memory dict loses history on restart and won't work across
multiple backend replicas.
"""

from typing import Any

_sessions: dict[str, list[dict[str, Any]]] = {}

MAX_TURNS_KEPT = 20  


def get_history(session_id: str) -> list[dict[str, Any]]:
    return _sessions.setdefault(session_id, [])


def append_and_trim(session_id: str, messages: list[dict[str, Any]]) -> None:
    history = get_history(session_id)
    history.extend(messages)
    if len(history) > MAX_TURNS_KEPT:
        del history[: len(history) - MAX_TURNS_KEPT]


def clear(session_id: str) -> None:
    _sessions.pop(session_id, None)
