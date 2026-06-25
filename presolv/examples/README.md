# Example conversations

Eight scripted demos mapping to the assessment rubric. Each resets mock data before running.

| Script | Scenario | Rubric |
|--------|----------|--------|
| `example_01_list_calendar.py` | "What's on my calendar tomorrow?" | Correct tool selection (read) |
| `example_02_multiturn_booking.py` | 2pm meeting → reschedule to 4pm → confirm | Multi-turn context + calendar chain |
| `example_03_calculator.py` | Minutes between 9:00 and 17:30 | Calculator only (no calendar/CRM) |
| `example_04_calendar_500.py` | Availability on 2025-06-20 | Tool error (SERVER_ERROR) handling |
| `example_05_ambiguous_sarah.py` | "Schedule time with Sarah" | Ambiguous input |
| `example_06_wrong_tool_recovery.py` | "Convert 50 miles to kilometers" | Recovery / correct tool routing |
| `example_07_no_tool.py` | "What can you help me with?" | No tool — direct answer |
| `example_08_not_found.py` | "Look up nobody@corp.com" | CRM NOT_FOUND handling |

Run all:

```bash
python examples/run_all.py
```

Works with **`MOCK_AGENT=true`** (no API key) or with a valid **`GEMINI_API_KEY`** for live Gemini routing.

Captured output: see [`transcripts/run_all.txt`](transcripts/run_all.txt).
