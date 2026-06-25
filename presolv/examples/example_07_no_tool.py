#!/usr/bin/env python3
"""Example 7: No tool — direct capability answer."""

from _runner import run_conversation

if __name__ == "__main__":
    run_conversation(
        title="Example 07 — No tool (capabilities question)",
        turns=["What can you help me with?"],
        session_id="example_07",
    )
