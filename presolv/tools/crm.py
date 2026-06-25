"""CRM contact lookup tool."""

from __future__ import annotations

from typing import Any

from data.fixtures import FixtureStore
from tools.base import BaseTool, ToolResult


class LookupContactTool(BaseTool):
    name = "lookup_contact"
    description = (
        "Look up a contact by name or email and return their profile plus recent "
        "interactions. Use when the user asks about a person, attendee, or client. "
        "Do NOT use for calendar scheduling, availability, or math/unit conversion."
    )
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Contact name (full or partial) or email address.",
            },
        },
        "required": ["query"],
    }

    def __init__(self, fixtures: FixtureStore) -> None:
        self._fixtures = fixtures

    def run(self, **kwargs: Any) -> ToolResult:
        query = kwargs["query"]
        ok, data, code = self._fixtures.lookup_contact(query)

        if code == "NOT_FOUND":
            return ToolResult(
                success=False,
                error=f"No contact found matching '{query}'.",
                code="NOT_FOUND",
            )
        if code == "AMBIGUOUS":
            return ToolResult(
                success=False,
                data=data,
                error="Multiple contacts match. Ask the user to clarify.",
                code="AMBIGUOUS",
            )
        return ToolResult(success=True, data={"contact": data})
