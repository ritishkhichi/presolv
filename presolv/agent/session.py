"""In-memory session store for conversation history."""

from __future__ import annotations

from dataclasses import dataclass, field

from google.genai import types


@dataclass
class Session:
    id: str
    contents: list[types.Content] = field(default_factory=list)


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}

    def get_or_create(self, session_id: str) -> Session:
        if session_id not in self._sessions:
            self._sessions[session_id] = Session(id=session_id)
        return self._sessions[session_id]

    def clear(self, session_id: str) -> None:
        if session_id in self._sessions:
            del self._sessions[session_id]

    def save(self, session: Session) -> None:
        self._sessions[session.id] = session
