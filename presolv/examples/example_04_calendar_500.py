#!/usr/bin/env python3
"""Example 4: Calendar SERVER_ERROR on poison date."""

from _runner import run_conversation

if __name__ == "__main__":
    run_conversation(
        title="Example 04 — Calendar 500 error (2025-06-20)",
        turns=[
            "Am I free on June 20th at 2pm for a 30-minute meeting?",
        ],
        session_id="example_04",
    )
