# Presolv Conversational Agent

Executive scheduling assistant with Gemini tool calling — calendar, CRM, and calculator mocks.

## Setup

Python 3.12+. Mock tools run locally without an API key.

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
copy .env.example .env        # Windows
# cp .env.example .env        # macOS/Linux
```

Edit `.env` and set your Gemini API key (or run fully offline):

```
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.0-flash
MOCK_TODAY=2025-06-18
MOCK_AGENT=true
```

**Offline mode:** Set `MOCK_AGENT=true` (or leave `GEMINI_API_KEY` empty) to use a rule-based mock agent with the same **mocked tools** (calendar, CRM, calculator). This matches the assessment brief — tools are fake; the agent still decides which tool to call.

## Run the CLI

From the project root:

```bash
python cli.py
```

Commands inside the REPL:

- `/reset` — clear conversation history and restore mock calendar/CRM data
- `/quit` — exit

## Run example conversations

```bash
python examples/example_01_list_calendar.py
python examples/run_all.py
```

Pre-captured output: [`examples/transcripts/run_all.txt`](examples/transcripts/run_all.txt)

## Submission

- [`prompts.md`](prompts.md) — AI build transcripts summary
- [`NOTES.md`](NOTES.md) — approach and tradeoffs
- [`LOOM_SCRIPT.md`](LOOM_SCRIPT.md) — outline for your 5-minute video

## Architecture

A single **AgentOrchestrator** runs a manual tool-calling loop against Gemini (automatic function calling disabled). When `MOCK_AGENT=true` or no API key is set, a **MockAgentOrchestrator** drives the same tools with rule-based routing for offline demos.

Five tools wrap an in-memory **FixtureStore** for calendar and CRM data plus a safe **calculate** tool. Conversation history is stored per session in **SessionStore**.

```
cli.py / examples/* → agent/orchestrator.py OR agent/mock_orchestrator.py → tools/* → data/fixtures.py
```

## Tools

| Tool | Purpose |
|------|---------|
| `list_calendar_events` | List events in a date range |
| `check_calendar_availability` | Check if a slot is free |
| `create_calendar_event` | Book a meeting (after user confirmation) |
| `lookup_contact` | CRM lookup by name or email |
| `calculate` | Math and unit conversions |

## Mock data notes

- **Today** is fixed to `2025-06-18` (UTC) unless `MOCK_TODAY` is changed.
- **Poison date** `2025-06-20` simulates a calendar API 500 on availability checks.
- Querying CRM for **"Sarah"** returns an ambiguous match (Sarah Chen vs Sarah Patel).

## Project layout

```
presolv/
├── agent/          # orchestrator, session, prompts, Gemini client
├── tools/          # tool registry and implementations
├── data/           # mock fixtures
├── examples/       # six scripted demos
├── cli.py          # interactive REPL
└── bootstrap.py    # shared wiring
```
