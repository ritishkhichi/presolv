"""Shared helper for running scripted example conversations."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bootstrap import create_orchestrator, get_fixtures, validate_api_key


def run_conversation(
    title: str,
    turns: list[str],
    session_id: str,
) -> list[str]:
    validate_api_key()
    fixtures = get_fixtures()
    fixtures.reset()
    orchestrator = create_orchestrator()

    print("=" * 60)
    print(title)
    print("=" * 60)

    replies: list[str] = []
    for turn in turns:
        print(f"\nUSER: {turn}")
        reply = orchestrator.run_turn(session_id, turn)
        replies.append(reply)
        print(f"ASSISTANT: {reply}")

    print()
    return replies
