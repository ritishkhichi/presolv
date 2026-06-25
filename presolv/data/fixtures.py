"""In-memory mock calendar and CRM data with deterministic poison rules."""

from __future__ import annotations

import copy
import os
from dataclasses import dataclass, field
from datetime import date, datetime


POISON_DATE = "2025-06-20"


def get_mock_today() -> date:
    raw = os.getenv("MOCK_TODAY", "2025-06-18")
    return date.fromisoformat(raw)


@dataclass
class CalendarEvent:
    id: str
    title: str
    date: str
    start_time: str
    duration_minutes: int
    attendee_email: str | None = None


@dataclass
class Interaction:
    date: str
    type: str
    summary: str


@dataclass
class Contact:
    id: str
    name: str
    email: str
    company: str
    recent_interactions: list[Interaction] = field(default_factory=list)


def _seed_calendar() -> list[CalendarEvent]:
    return [
        CalendarEvent(
            id="evt-1",
            title="Executive standup",
            date="2025-06-18",
            start_time="09:00",
            duration_minutes=30,
        ),
        CalendarEvent(
            id="evt-2",
            title="Product review with John Smith",
            date="2025-06-18",
            start_time="11:00",
            duration_minutes=60,
            attendee_email="john.smith@acmecorp.com",
        ),
        CalendarEvent(
            id="evt-3",
            title="Board prep",
            date="2025-06-18",
            start_time="15:00",
            duration_minutes=90,
        ),
        CalendarEvent(
            id="evt-4",
            title="Client sync with John Smith",
            date="2025-06-19",
            start_time="14:00",
            duration_minutes=60,
            attendee_email="john.smith@acmecorp.com",
        ),
        CalendarEvent(
            id="evt-5",
            title="Team 1:1",
            date="2025-06-19",
            start_time="10:00",
            duration_minutes=30,
        ),
        CalendarEvent(
            id="evt-6",
            title="Investor call",
            date="2025-06-21",
            start_time="16:00",
            duration_minutes=45,
        ),
    ]


def _seed_contacts() -> list[Contact]:
    return [
        Contact(
            id="crm-1",
            name="John Smith",
            email="john.smith@acmecorp.com",
            company="Acme Corp",
            recent_interactions=[
                Interaction("2025-06-10", "email", "Discussed Q3 roadmap"),
                Interaction("2025-06-05", "meeting", "Quarterly business review"),
            ],
        ),
        Contact(
            id="crm-2",
            name="Sarah Chen",
            email="sarah.chen@techstart.io",
            company="TechStart",
            recent_interactions=[
                Interaction("2025-06-12", "call", "Partnership discussion"),
                Interaction("2025-06-01", "email", "Sent proposal draft"),
            ],
        ),
        Contact(
            id="crm-3",
            name="Sarah Patel",
            email="sarah.patel@globalinc.com",
            company="Global Inc",
            recent_interactions=[
                Interaction("2025-06-08", "meeting", "Contract negotiation"),
            ],
        ),
        Contact(
            id="crm-4",
            name="Emily Watson",
            email="emily.watson@designco.com",
            company="Design Co",
            recent_interactions=[
                Interaction("2025-06-14", "email", "Design review feedback"),
            ],
        ),
        Contact(
            id="crm-5",
            name="Michael Torres",
            email="m.torres@financehub.com",
            company="FinanceHub",
            recent_interactions=[
                Interaction("2025-06-11", "call", "Budget alignment"),
                Interaction("2025-06-03", "meeting", "Annual planning"),
            ],
        ),
        Contact(
            id="crm-6",
            name="Lisa Park",
            email="lisa.park@healthplus.org",
            company="HealthPlus",
            recent_interactions=[
                Interaction("2025-06-07", "email", "Compliance update"),
            ],
        ),
    ]


class FixtureStore:
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.calendar_events: list[CalendarEvent] = copy.deepcopy(_seed_calendar())
        self.contacts: list[Contact] = copy.deepcopy(_seed_contacts())
        self._next_event_id = 100

    def list_events(self, start_date: str, end_date: str) -> list[dict]:
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
        results = []
        for evt in self.calendar_events:
            evt_date = date.fromisoformat(evt.date)
            if start <= evt_date <= end:
                results.append(self._event_to_dict(evt))
        return sorted(results, key=lambda e: (e["date"], e["start_time"]))

    def check_availability(
        self, date_str: str, start_time: str, duration_minutes: int
    ) -> tuple[bool, dict | None, str | None]:
        if date_str == POISON_DATE:
            return False, None, "SERVER_ERROR"

        conflicts = self._find_conflicts(date_str, start_time, duration_minutes)
        if conflicts:
            return False, {"available": False, "conflicts": conflicts}, "CONFLICT"
        return True, {"available": True, "conflicts": []}, None

    def create_event(
        self,
        title: str,
        date_str: str,
        start_time: str,
        duration_minutes: int,
        attendee_email: str | None = None,
    ) -> tuple[bool, dict | None, str | None]:
        ok, data, code = self.check_availability(date_str, start_time, duration_minutes)
        if not ok and code == "SERVER_ERROR":
            return False, None, "SERVER_ERROR"
        if not ok:
            return False, data, "CONFLICT"

        self._next_event_id += 1
        evt = CalendarEvent(
            id=f"evt-{self._next_event_id}",
            title=title,
            date=date_str,
            start_time=start_time,
            duration_minutes=duration_minutes,
            attendee_email=attendee_email,
        )
        self.calendar_events.append(evt)
        return True, self._event_to_dict(evt), None

    def lookup_contact(self, query: str) -> tuple[bool, dict | None, str | None]:
        query_stripped = query.strip()
        query_lower = query_stripped.lower()

        if "@" in query_lower:
            for contact in self.contacts:
                if contact.email.lower() == query_lower:
                    return True, self._contact_to_dict(contact), None
            return False, None, "NOT_FOUND"

        matches = [
            c
            for c in self.contacts
            if query_lower in c.name.lower() or c.name.lower() == query_lower
        ]

        if not matches:
            first_name_matches = [
                c for c in self.contacts if c.name.lower().split()[0] == query_lower
            ]
            matches = first_name_matches

        if not matches:
            return False, None, "NOT_FOUND"

        if len(matches) == 1:
            return True, self._contact_to_dict(matches[0]), None

        if query_lower == "sarah":
            candidates = [self._contact_summary(c) for c in matches]
            return False, {"candidates": candidates}, "AMBIGUOUS"

        if len(matches) > 1:
            candidates = [self._contact_summary(c) for c in matches]
            return False, {"candidates": candidates}, "AMBIGUOUS"

        return True, self._contact_to_dict(matches[0]), None

    def _find_conflicts(
        self, date_str: str, start_time: str, duration_minutes: int
    ) -> list[dict]:
        new_start = self._time_to_minutes(start_time)
        new_end = new_start + duration_minutes
        conflicts = []
        for evt in self.calendar_events:
            if evt.date != date_str:
                continue
            evt_start = self._time_to_minutes(evt.start_time)
            evt_end = evt_start + evt.duration_minutes
            if new_start < evt_end and new_end > evt_start:
                conflicts.append(self._event_to_dict(evt))
        return conflicts

    @staticmethod
    def _time_to_minutes(time_str: str) -> int:
        parts = time_str.split(":")
        return int(parts[0]) * 60 + int(parts[1])

    @staticmethod
    def _event_to_dict(evt: CalendarEvent) -> dict:
        return {
            "id": evt.id,
            "title": evt.title,
            "date": evt.date,
            "start_time": evt.start_time,
            "duration_minutes": evt.duration_minutes,
            "attendee_email": evt.attendee_email,
        }

    def _contact_to_dict(self, contact: Contact) -> dict:
        return {
            "id": contact.id,
            "name": contact.name,
            "email": contact.email,
            "company": contact.company,
            "recent_interactions": [
                {"date": i.date, "type": i.type, "summary": i.summary}
                for i in contact.recent_interactions
            ],
        }

    def _contact_summary(self, contact: Contact) -> dict:
        return {
            "id": contact.id,
            "name": contact.name,
            "email": contact.email,
            "company": contact.company,
        }
