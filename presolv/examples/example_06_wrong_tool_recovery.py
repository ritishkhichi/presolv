#!/usr/bin/env python3
"""Example 6: Wrong-tool recovery — unit conversion via calculator."""

from _runner import run_conversation

if __name__ == "__main__":
    run_conversation(
        title="Example 06 — Wrong-tool recovery (miles to km)",
        turns=["Convert 50 miles to kilometers."],
        session_id="example_06",
    )
