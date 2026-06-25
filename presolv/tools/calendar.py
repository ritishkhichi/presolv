"""Calendar tools backed by FixtureStore."""

from __future__ import annotations

from typing import Any

from data.fixtures import FixtureStore
from tools.base import BaseTool, ToolResult


class ListCalendarEventsTool(BaseTool):
    name = "list_calendar_events"
    description = (
        "List calendar events within a date range (inclusive). "
        "Use when the user asks what is on their schedule, agenda, or calendar. "
        "Do NOT use for checking if a specific time slot is free — use "
        "check_calendar_availability instead. Do NOT use for math or contact lookup."
    )
    parameters = {
        "type": "object",
        "properties": {
            "start_date": {
                "type": "string",
                "description": "Start date in ISO format YYYY-MM-DD (UTC).",
            },
            "end_date": {
                "type": "string",
                "description": "End date in ISO format YYYY-MM-DD (UTC).",
            },
        },
        "required": ["start_date", "end_date"],
    }

    def __init__(self, fixtures: FixtureStore) -> None:
        self._fixtures = fixtures

    def run(self, **kwargs: Any) -> ToolResult:
        start_date = kwargs["start_date"]
        end_date = kwargs["end_date"]
        events = self._fixtures.list_events(start_date, end_date)
        return ToolResult(
            success=True,
            data={"events": events, "count": len(events)},
        )


class CheckCalendarAvailabilityTool(BaseTool):
    name = "check_calendar_availability"
    description = (
        "Check whether a specific time slot is free on the calendar. "
        "Use before scheduling or rescheduling meetings. "
        "Do NOT use to list all events — use list_calendar_events instead. "
        "Do NOT use for contact lookup or calculations."
    )
    parameters = {
        "type": "object",
        "properties": {
            "date": {
                "type": "string",
                "description": "Date in ISO format YYYY-MM-DD (UTC).",
            },
            "start_time": {
                "type": "string",
                "description": "Start time in 24-hour HH:MM format (UTC).",
            },
            "duration_minutes": {
                "type": "integer",
                "description": "Meeting duration in minutes.",
            },
        },
        "required": ["date", "start_time", "duration_minutes"],
    }

    def __init__(self, fixtures: FixtureStore) -> None:
        self._fixtures = fixtures

    def run(self, **kwargs: Any) -> ToolResult:
        date_str = kwargs["date"]
        start_time = kwargs["start_time"]
        duration_minutes = int(kwargs["duration_minutes"])

        ok, data, code = self._fixtures.check_availability(
            date_str, start_time, duration_minutes
        )
        if code == "SERVER_ERROR":
            return ToolResult(
                success=False,
                error="Calendar service is temporarily unavailable (HTTP 500).",
                code="SERVER_ERROR",
            )
        if not ok:
            return ToolResult(
                success=False,
                data=data,
                error="The requested time slot conflicts with existing events.",
                code=code,
            )
        return ToolResult(success=True, data=data)


class CreateCalendarEventTool(BaseTool):
    name = "create_calendar_event"
    description = (
        "Create a new calendar event. ONLY use after confirming title, date, time, "
        "duration, and attendee (if any) with the user, and after checking availability. "
        "Do NOT use for listing events, checking availability, CRM lookup, or math."
    )
    parameters = {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Meeting title."},
            "date": {
                "type": "string",
                "description": "Date in ISO format YYYY-MM-DD (UTC).",
            },
            "start_time": {
                "type": "string",
                "description": "Start time in 24-hour HH:MM format (UTC).",
            },
            "duration_minutes": {
                "type": "integer",
                "description": "Meeting duration in minutes.",
            },
            "attendee_email": {
                "type": "string",
                "description": "Optional attendee email address.",
            },
        },
        "required": ["title", "date", "start_time", "duration_minutes"],
    }

    def __init__(self, fixtures: FixtureStore) -> None:
        self._fixtures = fixtures

    def run(self, **kwargs: Any) -> ToolResult:
        title = kwargs["title"]
        date_str = kwargs["date"]
        start_time = kwargs["start_time"]
        duration_minutes = int(kwargs["duration_minutes"])
        attendee_email = kwargs.get("attendee_email")

        ok, data, code = self._fixtures.create_event(
            title, date_str, start_time, duration_minutes, attendee_email
        )
        if code == "SERVER_ERROR":
            return ToolResult(
                success=False,
                error="Calendar service is temporarily unavailable (HTTP 500).",
                code="SERVER_ERROR",
            )
        if not ok:
            return ToolResult(
                success=False,
                data=data,
                error="Could not create event due to a scheduling conflict.",
                code=code,
            )
        return ToolResult(success=True, data={"event": data})
