#!/usr/bin/env python3
"""Example 3: Calculator only — no calendar or CRM."""

from _runner import run_conversation

if __name__ == "__main__":
    run_conversation(
        title="Example 03 — Calculator (no calendar/CRM)",
        turns=["How many minutes between 9:00 and 17:30?"],
        session_id="example_03",
    )
