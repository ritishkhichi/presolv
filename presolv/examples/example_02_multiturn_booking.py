#!/usr/bin/env python3
"""Example 2: Multi-turn booking with context and confirmation."""

from _runner import run_conversation

if __name__ == "__main__":
    run_conversation(
        title="Example 02 — Multi-turn reschedule",
        turns=[
            "Who is my 2pm meeting with tomorrow?",
            "Reschedule it to 4pm.",
            "Yes, please confirm that change.",
        ],
        session_id="example_02",
    )
