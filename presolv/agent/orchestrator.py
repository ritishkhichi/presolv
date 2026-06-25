"""Agent orchestrator with manual multi-tool calling loop."""

from __future__ import annotations

import logging
from typing import Optional

from google.genai import types

from agent.gemini_client import GeminiClient
from agent.prompts import build_system_prompt
from agent.session import SessionStore
from data.fixtures import get_mock_today
from tools.base import ToolRegistry

logger = logging.getLogger(__name__)

MAX_TOOL_ROUNDS = 8


class AgentOrchestrator:
    def __init__(
        self,
        registry: ToolRegistry,
        session_store: SessionStore,
        gemini_client: Optional[GeminiClient] = None,
    ) -> None:
        self._registry = registry
        self._sessions = session_store
        self._gemini = gemini_client or GeminiClient()
        self._system_prompt = build_system_prompt(get_mock_today())

    def clear_session(self, session_id: str) -> None:
        self._sessions.clear(session_id)

    def run_turn(self, session_id: str, user_text: str) -> str:
        session = self._sessions.get_or_create(session_id)
        session.contents.append(
            types.Content(role="user", parts=[types.Part(text=user_text)])
        )

        tool_rounds = 0
        while tool_rounds < MAX_TOOL_ROUNDS:
            try:
                response = self._gemini.generate(
                    contents=session.contents,
                    tool_declarations=self._registry.declarations(),
                    system_instruction=self._system_prompt,
                )
            except RuntimeError as exc:
                fallback = (
                    "I'm sorry, I encountered an issue connecting to the AI service. "
                    "Please try again in a moment."
                )
                session.contents.append(
                    types.Content(role="model", parts=[types.Part(text=fallback)])
                )
                self._sessions.save(session)
                return f"{fallback} ({exc})"

            if not response.candidates:
                fallback = "I wasn't able to generate a response. Please try again."
                session.contents.append(
                    types.Content(role="model", parts=[types.Part(text=fallback)])
                )
                self._sessions.save(session)
                return fallback

            candidate = response.candidates[0]
            if not candidate.content or not candidate.content.parts:
                fallback = "I wasn't able to generate a response. Please try again."
                session.contents.append(
                    types.Content(role="model", parts=[types.Part(text=fallback)])
                )
                self._sessions.save(session)
                return fallback

            parts = candidate.content.parts
            function_calls = [p for p in parts if p.function_call]

            if not function_calls:
                text = response.text or ""
                session.contents.append(
                    types.Content(role="model", parts=[types.Part(text=text)])
                )
                self._sessions.save(session)
                return text

            response_parts: list[types.Part] = []
            for part in parts:
                if part.text:
                    response_parts.append(types.Part(text=part.text))
                if part.function_call:
                    response_parts.append(part)

            session.contents.append(
                types.Content(role="model", parts=response_parts)
            )

            function_response_parts: list[types.Part] = []
            for fc_part in function_calls:
                fc = fc_part.function_call
                if fc is None:
                    continue
                name = fc.name or ""
                args = dict(fc.args) if fc.args else {}
                result = self._registry.execute(name, args)
                logger.info(
                    "Tool call: %s args=%s success=%s code=%s",
                    name,
                    args,
                    result.success,
                    result.code,
                )
                response_payload = self._registry.result_to_response(result)
                fc_id = getattr(fc_part, "id", None) or getattr(fc, "id", None)
                function_response_parts.append(
                    types.Part.from_function_response(
                        name=name,
                        response=response_payload,
                        id=fc_id,
                    )
                )

            session.contents.append(
                types.Content(role="user", parts=function_response_parts)
            )
            tool_rounds += 1

        fallback = (
            "I need a bit more information to complete that request. "
            "Could you clarify what you'd like me to do?"
        )
        session.contents.append(
            types.Content(role="model", parts=[types.Part(text=fallback)])
        )
        self._sessions.save(session)
        return fallback
