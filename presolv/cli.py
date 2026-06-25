#!/usr/bin/env python3
"""Interactive CLI for the Presolv executive scheduling assistant."""

from __future__ import annotations

from bootstrap import create_orchestrator, get_fixtures, use_mock_agent, validate_api_key
from data.fixtures import get_mock_today

SESSION_ID = "default"


def main() -> None:
    validate_api_key()
    orchestrator = create_orchestrator()
    fixtures = get_fixtures()

    mode = "mock (offline)" if use_mock_agent() else "Gemini"
    print("Presolv Executive Scheduling Assistant")
    print(f"Mode: {mode}")
    print(f"Mock today: {get_mock_today().isoformat()} (UTC)")
    print("Commands: /reset  /quit")
    print("-" * 50)

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if not user_input:
            continue
        if user_input.lower() in ("/quit", "/exit", "quit", "exit"):
            print("Goodbye.")
            break
        if user_input.lower() == "/reset":
            orchestrator.clear_session(SESSION_ID)
            fixtures.reset()
            print("Session and calendar data reset.")
            continue

        reply = orchestrator.run_turn(SESSION_ID, user_input)
        print(f"\nAssistant: {reply}")


if __name__ == "__main__":
    main()
