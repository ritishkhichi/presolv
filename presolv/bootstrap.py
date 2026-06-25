"""Shared wiring for CLI and example scripts."""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import Union

from dotenv import load_dotenv

from agent.gemini_client import GeminiClient
from agent.mock_orchestrator import MockAgentOrchestrator
from agent.orchestrator import AgentOrchestrator
from agent.session import SessionStore
from data.fixtures import FixtureStore
from tools.base import build_registry

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

Orchestrator = Union[AgentOrchestrator, MockAgentOrchestrator]


def use_mock_agent() -> bool:
    """Use offline mock agent when MOCK_AGENT=true or no API key is set."""
    flag = os.getenv("MOCK_AGENT", "").lower()
    if flag in ("1", "true", "yes"):
        return True
    if flag in ("0", "false", "no"):
        return False
    return not os.getenv("GEMINI_API_KEY")


@lru_cache(maxsize=1)
def get_fixtures() -> FixtureStore:
    return FixtureStore()


def create_orchestrator(reset_fixtures: bool = False) -> Orchestrator:
    fixtures = get_fixtures()
    if reset_fixtures:
        fixtures.reset()
    registry = build_registry(fixtures)
    session_store = SessionStore()

    if use_mock_agent():
        logging.getLogger(__name__).info("Using mock agent (no Gemini API)")
        return MockAgentOrchestrator(registry, session_store)

    client = GeminiClient()
    return AgentOrchestrator(registry, session_store, client)


def validate_api_key() -> None:
    if use_mock_agent():
        return
    if not os.getenv("GEMINI_API_KEY"):
        raise SystemExit(
            "GEMINI_API_KEY is not set. Copy .env.example to .env and add your key, "
            "or set MOCK_AGENT=true to run offline with the mock agent."
        )
