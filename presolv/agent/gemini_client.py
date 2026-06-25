"""Thin wrapper around the Google GenAI client."""

from __future__ import annotations

import logging
import os
from typing import Any, Optional

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


def create_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set.")
    return genai.Client(api_key=api_key)


def get_model_name() -> str:
    return os.getenv("GEMINI_MODEL", "gemini-2.0-flash")


class GeminiClient:
    def __init__(self, client: Optional[genai.Client] = None) -> None:
        self._client = client or create_client()
        self._model = get_model_name()

    def generate(
        self,
        contents: list[types.Content],
        tool_declarations: list[types.FunctionDeclaration],
        system_instruction: str,
    ) -> types.GenerateContentResponse:
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=[types.Tool(function_declarations=tool_declarations)],
            automatic_function_calling=types.AutomaticFunctionCallingConfig(
                disable=True
            ),
        )
        try:
            return self._client.models.generate_content(
                model=self._model,
                contents=contents,
                config=config,
            )
        except Exception as exc:
            logger.exception("Gemini API error")
            raise RuntimeError(f"Gemini API error: {exc}") from exc
