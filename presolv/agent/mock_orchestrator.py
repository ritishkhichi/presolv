"""Rule-based agent for offline demos when Gemini API is unavailable.

Uses the same mocked tools (calendar, CRM, calculator) and demonstrates
tool selection, multi-turn context, errors, and confirmation flows.
"""

from __future__ import annotations

import logging
import re
from datetime import timedelta
from typing import Any, Optional

from agent.session import SessionStore
from data.fixtures import POISON_DATE, get_mock_today
from tools.base import ToolRegistry

logger = logging.getLogger(__name__)


class MockAgentOrchestrator:
    """Deterministic stand-in for AgentOrchestrator — no LLM required."""

    def __init__(self, registry: ToolRegistry, session_store: SessionStore) -> None:
        self._registry = registry
        self._sessions = session_store
        self._meta: dict[str, dict[str, Any]] = {}
        self._history: dict[str, list[str]] = {}

    def clear_session(self, session_id: str) -> None:
        self._sessions.clear(session_id)
        self._meta.pop(session_id, None)
        self._history.pop(session_id, None)

    def _meta_for(self, session_id: str) -> dict[str, Any]:
        if session_id not in self._meta:
            self._meta[session_id] = {}
        return self._meta[session_id]

    def _remember(self, session_id: str, user_text: str) -> None:
        self._history.setdefault(session_id, []).append(user_text.lower())

    def _tomorrow(self) -> str:
        return (get_mock_today() + timedelta(days=1)).isoformat()

    def _run_tool(self, name: str, args: dict[str, Any]) -> Any:
        result = self._registry.execute(name, args)
        logger.info(
            "Tool call: %s args=%s success=%s code=%s",
            name,
            args,
            result.success,
            result.code,
        )
        return result

    def run_turn(self, session_id: str, user_text: str) -> str:
        self._remember(session_id, user_text)
        text = user_text.lower().strip()
        meta = self._meta_for(session_id)

        if self._is_confirm(text) and meta.get("pending_action"):
            return self._execute_pending(meta)

        if self._is_greeting_or_help(text):
            return self._help_reply()

        if self._is_thanks(text):
            return (
                "You're welcome. Let me know if you need anything else "
                "on your calendar or contacts."
            )

        if self._is_june_20_query(text) or self._is_availability_query(text):
            if self._is_june_20_query(text):
                return self._handle_june_20()
            return self._handle_availability(text)

        if self._is_calculator_query(text):
            return self._handle_calculator(text)

        if self._is_sarah_scheduling(text):
            return self._handle_sarah()

        if self._is_reschedule(text, meta):
            return self._handle_reschedule(text, meta)

        if self._is_2pm_meeting_query(text):
            return self._handle_2pm_meeting(meta)

        if self._is_calendar_list_query(text):
            return self._handle_calendar_list(text)

        if self._is_crm_lookup(text):
            return self._handle_crm_lookup(text)

        if self._is_booking_request(text):
            return self._handle_booking(meta)

        return (
            "I can help with your calendar, CRM contacts, and quick calculations. "
            "Try asking what's on your calendar tomorrow, to look up a contact, "
            "or to convert units like miles to kilometers."
        )

    @staticmethod
    def _is_confirm(text: str) -> bool:
        return bool(
            re.search(
                r"^(yes|yeah|yep|confirm|go ahead|please confirm|sounds good|ok|okay)\b",
                text,
            )
        )

    @staticmethod
    def _is_greeting_or_help(text: str) -> bool:
        return bool(
            re.search(
                r"\b(what can you help|what do you do|capabilities|hello|hi)\b",
                text,
            )
        )

    @staticmethod
    def _is_thanks(text: str) -> bool:
        return bool(re.search(r"\b(thanks|thank you)\b", text))

    @staticmethod
    def _is_calculator_query(text: str) -> bool:
        if re.search(r"\b(minutes?\s+between|convert\b|miles?\s+to)\b", text):
            return True
        if re.search(r"\b(calculate|arithmetic)\b", text):
            return True
        return bool(re.search(r"\d+\s*[\+\-\*/]\s*\d+", text))

    @staticmethod
    def _is_availability_query(text: str) -> bool:
        return bool(
            re.search(r"\b(free|available|availability)\b", text)
        ) and bool(re.search(r"\b(at|on|for)\b", text))

    @staticmethod
    def _is_june_20_query(text: str) -> bool:
        return bool(re.search(r"june\s+20", text)) or "2025-06-20" in text

    @staticmethod
    def _is_sarah_scheduling(text: str) -> bool:
        return "sarah" in text and bool(
            re.search(r"\b(schedule|meeting|time with|book|set up)\b", text)
        )

    @staticmethod
    def _is_reschedule(text: str, meta: dict[str, Any]) -> bool:
        return bool(re.search(r"\b(reschedule|move)\b", text)) or (
            ("4pm" in text or "16:00" in text) and bool(meta.get("last_event"))
        )

    @staticmethod
    def _is_2pm_meeting_query(text: str) -> bool:
        return ("2pm" in text or "14:00" in text or "2 pm" in text) and bool(
            re.search(r"\b(who|meeting|with)\b", text)
        )

    @staticmethod
    def _is_calendar_list_query(text: str) -> bool:
        return bool(
            re.search(r"\b(calendar|schedule|agenda|what'?s on)\b", text)
        ) and bool(re.search(r"\b(tomorrow|today|thursday|friday)\b", text))

    @staticmethod
    def _is_crm_lookup(text: str) -> bool:
        return bool(re.search(r"\b(look\s*up|find)\b", text)) and (
            "@" in text or re.search(r"\b(john|smith|contact)\b", text)
        )

    @staticmethod
    def _extract_lookup_query(text: str) -> str:
        email_match = re.search(r"[\w.+-]+@[\w.-]+\.\w+", text)
        if email_match:
            return email_match.group(0)
        if "john" in text or "smith" in text:
            return "John Smith"
        return text.strip()

    @staticmethod
    def _is_booking_request(text: str) -> bool:
        return bool(re.search(r"\b(book|schedule)\b", text)) and "sarah" not in text

    def _help_reply(self) -> str:
        return (
            "I'm your executive scheduling assistant. I can:\n"
            "- List or check your calendar\n"
            "- Look up contacts in the CRM\n"
            "- Run quick calculations and unit conversions\n\n"
            "I'll always confirm details before booking a new meeting."
        )

    def _handle_calculator(self, text: str) -> str:
        expr = text.strip().rstrip(".?")
        if "convert" in text:
            expr = re.sub(r"^convert\s+", "", expr, flags=re.I)
        elif "how many minutes between" in text:
            expr = text.replace("how many", "").strip().rstrip(".?")

        result = self._run_tool("calculate", {"expression": expr})
        if not result.success:
            return f"I couldn't calculate that: {result.error}"

        data = result.data or {}
        value = data.get("result")
        unit = data.get("unit", "")
        if unit:
            return f"The result is {value} {unit}."
        return f"The result is {value}."

    def _handle_june_20(self) -> str:
        result = self._run_tool(
            "check_calendar_availability",
            {"date": POISON_DATE, "start_time": "14:00", "duration_minutes": 30},
        )
        if result.code == "SERVER_ERROR":
            return (
                "I'm sorry — the calendar service is temporarily unavailable "
                "(server error). I wasn't able to check your availability on "
                "June 20th. Please try again later or choose a different date."
            )
        return "Unexpected response from calendar."

    def _handle_availability(self, text: str) -> str:
        date_str = POISON_DATE if "june 20" in text else self._tomorrow()
        result = self._run_tool(
            "check_calendar_availability",
            {"date": date_str, "start_time": "14:00", "duration_minutes": 30},
        )
        if result.code == "SERVER_ERROR":
            return (
                "I'm sorry — the calendar service is temporarily unavailable "
                "(server error). I wasn't able to check your availability. "
                "Please try again later or choose a different date."
            )
        if result.success:
            return "That time slot is available on your calendar."
        return f"That slot is not available: {result.error}"

    def _handle_sarah(self) -> str:
        result = self._run_tool("lookup_contact", {"query": "Sarah"})
        if result.code == "AMBIGUOUS":
            candidates = (result.data or {}).get("candidates", [])
            lines = ["I found multiple contacts named Sarah. Which one did you mean?\n"]
            for c in candidates:
                lines.append(f"- {c['name']} ({c['email']}) at {c['company']}")
            lines.append("\nPlease let me know which Sarah you'd like to meet with.")
            return "\n".join(lines)
        return "I couldn't look up that contact."

    def _handle_2pm_meeting(self, meta: dict[str, Any]) -> str:
        tomorrow = self._tomorrow()
        result = self._run_tool(
            "list_calendar_events",
            {"start_date": tomorrow, "end_date": tomorrow},
        )
        events = (result.data or {}).get("events", [])
        match = next(
            (e for e in events if e["start_time"] in ("14:00", "2:00")),
            None,
        )
        if not match:
            return f"I don't see a 2pm meeting on your calendar for tomorrow ({tomorrow})."

        meta["last_event"] = match
        attendee = match.get("attendee_email") or "no external attendee listed"
        if match.get("attendee_email"):
            crm = self._run_tool("lookup_contact", {"query": match["attendee_email"]})
            if crm.success:
                contact = (crm.data or {}).get("contact", {})
                attendee = f"{contact['name']} ({contact['email']})"

        return (
            f"Tomorrow at 2:00 PM UTC you have {match['title']} "
            f"({match['duration_minutes']} min). The attendee is {attendee}."
        )

    def _handle_reschedule(self, text: str, meta: dict[str, Any]) -> str:
        event = meta.get("last_event")
        if not event:
            return "Which meeting would you like to reschedule?"

        new_time = "16:00"
        if re.search(r"3\s*pm|15:00", text):
            new_time = "15:00"

        tomorrow = event["date"]
        duration = event["duration_minutes"]
        check = self._run_tool(
            "check_calendar_availability",
            {
                "date": tomorrow,
                "start_time": new_time,
                "duration_minutes": duration,
            },
        )
        if not check.success:
            if check.code == "CONFLICT":
                return (
                    "4:00 PM tomorrow is not available — it conflicts with another event. "
                    "Would you like me to suggest another time?"
                )
            return f"I couldn't check availability: {check.error}"

        meta["pending_action"] = {
            "type": "reschedule",
            "title": event["title"],
            "date": tomorrow,
            "start_time": new_time,
            "duration_minutes": duration,
            "attendee_email": event.get("attendee_email"),
        }
        hour = int(new_time.split(":")[0])
        display = f"{hour - 12 if hour > 12 else hour}:00 PM"
        return (
            f"I can reschedule {event['title']} from 2:00 PM to "
            f"{display} UTC tomorrow ({tomorrow}). Shall I confirm this change?"
        )

    def _handle_calendar_list(self, text: str) -> str:
        if "tomorrow" in text:
            day = self._tomorrow()
        elif "today" in text:
            day = get_mock_today().isoformat()
        else:
            day = self._tomorrow()

        result = self._run_tool(
            "list_calendar_events",
            {"start_date": day, "end_date": day},
        )
        events = (result.data or {}).get("events", [])
        if not events:
            return f"You have nothing on your calendar for {day}."

        lines = [f"Here's your schedule for {day} (UTC):\n"]
        for e in events:
            lines.append(
                f"- {e['start_time']} — {e['title']} ({e['duration_minutes']} min)"
            )
        return "\n".join(lines)

    def _handle_crm_lookup(self, text: str) -> str:
        query = self._extract_lookup_query(text)
        result = self._run_tool("lookup_contact", {"query": query})
        if result.code == "NOT_FOUND":
            return (
                f"I couldn't find a contact matching '{query}'. "
                "Please check the spelling or try a different email address."
            )
        if result.code == "AMBIGUOUS":
            return self._handle_sarah()
        if not result.success:
            return f"I couldn't find that contact: {result.error}"

        c = (result.data or {}).get("contact", {})
        interactions = c.get("recent_interactions", [])
        lines = [
            f"{c['name']} — {c['email']} ({c['company']})\n",
            "Recent interactions:",
        ]
        for i in interactions:
            lines.append(f"- {i['date']}: {i['type']} — {i['summary']}")
        return "\n".join(lines)

    def _handle_booking(self, meta: dict[str, Any]) -> str:
        meta["pending_action"] = {
            "type": "create",
            "title": "Meeting with John Smith",
            "date": self._tomorrow(),
            "start_time": "15:00",
            "duration_minutes": 30,
            "attendee_email": "john.smith@acmecorp.com",
        }
        return (
            "Before I book that, please confirm:\n"
            f"- Title: Meeting with John Smith\n"
            f"- Date: {self._tomorrow()} (tomorrow)\n"
            "- Time: 15:00 UTC (30 min)\n"
            "- Attendee: john.smith@acmecorp.com\n\n"
            "Reply yes to confirm."
        )

    def _execute_pending(self, meta: dict[str, Any]) -> str:
        action = meta.pop("pending_action", None)
        if not action:
            return "There's nothing pending to confirm."

        result = self._run_tool(
            "create_calendar_event",
            {
                "title": action["title"],
                "date": action["date"],
                "start_time": action["start_time"],
                "duration_minutes": action["duration_minutes"],
                "attendee_email": action.get("attendee_email"),
            },
        )
        if not result.success:
            return f"I wasn't able to complete that: {result.error}"

        event = (result.data or {}).get("event", {})
        return (
            f"Done — I've scheduled {event.get('title', action['title'])} on "
            f"{event.get('date', action['date'])} at "
            f"{event.get('start_time', action['start_time'])} UTC."
        )
