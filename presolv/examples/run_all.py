#!/usr/bin/env python3
"""Run all example conversations sequentially."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

EXAMPLES = [
    "example_01_list_calendar.py",
    "example_02_multiturn_booking.py",
    "example_03_calculator.py",
    "example_04_calendar_500.py",
    "example_05_ambiguous_sarah.py",
    "example_06_wrong_tool_recovery.py",
    "example_07_no_tool.py",
    "example_08_not_found.py",
]


def main() -> None:
    examples_dir = Path(__file__).parent
    for name in EXAMPLES:
        path = examples_dir / name
        print(f"\n>>> Running {name}\n")
        result = subprocess.run([sys.executable, str(path)], check=False)
        if result.returncode != 0:
            sys.exit(result.returncode)
    print("\n>>> All examples completed.")


if __name__ == "__main__":
    main()
