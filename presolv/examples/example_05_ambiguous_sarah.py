#!/usr/bin/env python3
"""Example 5: Ambiguous CRM contact (two Sarahs)."""

from _runner import run_conversation

if __name__ == "__main__":
    run_conversation(
        title="Example 05 — Ambiguous Sarah",
        turns=["I'd like to schedule time with Sarah."],
        session_id="example_05",
    )
