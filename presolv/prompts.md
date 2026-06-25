# Build prompts and AI transcripts

Cursor AI-assisted build for the Presolv conversational agent assessment (S5.pdf).

---

## Session 1 — Architecture and planning

**User prompts (key decisions):**

1. *"Build a conversational agent with calendar, CRM, calculator — simplest approach that demonstrates good agent behavior? Discuss first, no code."*
   - Outcome: Single-agent tool-calling loop, 5–6 granular tools, mocked fixtures, CLI-first, executive scheduling persona.

2. *"Language: Python, Gemini API, hybrid UI?, executive scheduling assistant — challenge me on alternatives."*
   - Outcome: Python + `google-genai`, CLI only (no UI), Gemini Flash, sequential multi-tool handling (not concurrency), confirm-before-create.

3. *"High-level architecture, LLD, repo layout, tech stack, error handling, memory."*
   - Outcome: Full architecture doc — `agent/`, `tools/`, `data/`, structured `ToolResult`, poison dates, 6 examples.

4. *Pre-implementation questions answered:*
   - 6 examples (ambiguous Sarah + wrong-tool recovery)
   - Always confirm before `create_calendar_event`
   - Automated example scripts
   - `gemini-2.0-flash`, `MOCK_TODAY=2025-06-18`, UTC

**AI role:** Architecture partner — pushed back on dual UI, LangChain, and parallel tool execution for 2-hour scope.

---

## Session 2 — Implementation

**User prompt:** *"Implement the plan as specified."*

**What was built:**
- `data/fixtures.py` — mock calendar/CRM, poison rules (2025-06-20 → 500, Sarah → AMBIGUOUS)
- `tools/` — 5 tools + `ToolRegistry` + `ToolResult` contract
- `agent/orchestrator.py` — manual Gemini loop, AFC disabled, multi-tool turn handling
- `agent/session.py`, `agent/prompts.py`, `agent/gemini_client.py`
- `cli.py`, `bootstrap.py`, 6 example scripts + `run_all.py`
- `README.md`, `NOTES.md`, `prompts.md` stub

**Fixes during build:**
- Python 3.9 compatibility (`Optional[dict]` in `ToolResult`)
- `_runner.py` import: `get_fixtures` from `bootstrap`, not `data.fixtures`

---

## Session 3 — Mock agent + submission finish

**User prompts:**

1. *"Gemini API token exhausted — go to mock what the task told us."*
   - Added `agent/mock_orchestrator.py`, `MOCK_AGENT=true`, auto-fallback when no API key.

2. *"What have we done vs what remains?"*
   - Audit against S5.pdf rubric and submission checklist.

3. *"Submission finish plan — implement."*
   - Added examples 07 (no-tool) and 08 (CRM NOT_FOUND), docs sync, transcripts, `prompts.md`, git prep.

**What didn't work:**
- Gemini API quota exhausted before live example runs.
- Initial `_runner.py` wrong import (`get_fixtures` location).
- Mock agent routing bugs for June 20th and "miles to kilometers" (fixed with better intent matching).

---

## Key design prompts (defend in interview)

| Decision | Rationale |
|----------|-----------|
| Manual tool loop, AFC disabled | Explicit agent behavior for review/Loom; structured error flow |
| 5 granular tools | Wrong-tool recovery visible; clear schemas for model |
| CLI only, no UI | Brief doesn't require UI; scope judgment for 2-hour budget |
| Mocked tools in memory | Per brief; deterministic poison rules for evals |
| `MOCK_AGENT` fallback | Same tools offline when Gemini unavailable |

---

