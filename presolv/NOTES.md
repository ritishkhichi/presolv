# Notes

## Approach

Built a minimal Python CLI agent with an explicit manual tool-calling loop (Gemini automatic function calling disabled). Five well-scoped tools wrap deterministic in-memory mocks. Structured `ToolResult` responses with error codes let the model handle failures, ambiguity, and wrong-tool recovery without hallucinating data.

**Gemini vs mock agent:** The primary design uses Gemini (`agent/orchestrator.py`) for autonomous tool routing. A rule-based `MockAgentOrchestrator` was added when API quota was exhausted — it calls the same mocked tools and supports offline demos via `MOCK_AGENT=true`. The brief requires mocked tools, not a live LLM; both paths satisfy that.

## Tradeoffs

- **CLI only** — no web UI (intentional scope choice; Loom demos the REPL).
- **In-memory fixtures** — no database; calendar mutations reset between examples.
- **Mock agent mode** — when `MOCK_AGENT=true` or no API key, a rule-based agent drives the same mocked tools offline (for demos without Gemini quota).
- **Sequential tool execution** — multiple tool calls in one turn are handled in a loop, not concurrently (fine for microsecond mocks).
- **Prompt-driven confirmation** — create events only after user confirms; not enforced by a hard state machine.

## If this were production

- Real Google Calendar / CRM APIs with OAuth, retries, and circuit breakers.
- Persistent sessions and audit logging.
- Structured observability (trace IDs per turn, tool latency metrics).
- Eval harness with golden transcripts and regression CI.
- Auth and multi-tenant session isolation.
- Rate limiting and input validation at the API boundary.
- Optional conversation summarization for long threads.

## Assumptions

- All times are UTC.
- `MOCK_TODAY=2025-06-18` anchors relative dates for reproducible demos.
- Gemini `gemini-2.0-flash` is sufficient for tool routing; model name is env-configurable.
