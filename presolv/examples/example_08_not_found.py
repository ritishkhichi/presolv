#!/usr/bin/env python3
"""Example 8: CRM NOT_FOUND — no matching contact."""

from _runner import run_conversation

if __name__ == "__main__":
    run_conversation(
        title="Example 08 — CRM NOT_FOUND",
        turns=["Look up nobody@corp.com"],
        session_id="example_08",
    )
