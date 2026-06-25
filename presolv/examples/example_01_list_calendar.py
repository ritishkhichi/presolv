#!/usr/bin/env python3
"""Example 1: List calendar events (happy path)."""

from _runner import run_conversation

if __name__ == "__main__":
    run_conversation(
        title="Example 01 — List calendar (happy path)",
        turns=["What's on my calendar tomorrow?"],
        session_id="example_01",
    )
