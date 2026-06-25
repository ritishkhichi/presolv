"""Tool registry, shared contracts, and Gemini function declarations."""

from __future__ import annotations  # noqa: I001

import logging
from abc import ABC, abstractmethod
from typing import Any, Optional

from google.genai import types
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)


class ToolResult(BaseModel):
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None
    code: Optional[str] = None


class BaseTool(ABC):
    name: str
    description: str
    parameters: dict[str, Any]

    @abstractmethod
    def run(self, **kwargs: Any) -> ToolResult:
        pass

    def to_declaration(self) -> types.FunctionDeclaration:
        return types.FunctionDeclaration(
            name=self.name,
            description=self.description,
            parameters=self.parameters,
        )


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool

    def declarations(self) -> list[types.FunctionDeclaration]:
        return [tool.to_declaration() for tool in self._tools.values()]

    def execute(self, name: str, args: dict[str, Any]) -> ToolResult:
        tool = self._tools.get(name)
        if tool is None:
            return ToolResult(
                success=False,
                error=f"Unknown tool: {name}",
                code="VALIDATION_ERROR",
            )
        try:
            return tool.run(**args)
        except ValidationError as exc:
            return ToolResult(
                success=False,
                error=str(exc),
                code="VALIDATION_ERROR",
            )
        except Exception as exc:
            logger.exception("Tool %s failed", name)
            return ToolResult(
                success=False,
                error=str(exc),
                code="SERVER_ERROR",
            )

    @staticmethod
    def result_to_response(result: ToolResult) -> dict[str, Any]:
        return result.model_dump(exclude_none=True)


def build_registry(fixtures: Any) -> ToolRegistry:
    from tools.calculator import CalculateTool
    from tools.calendar import (
        CheckCalendarAvailabilityTool,
        CreateCalendarEventTool,
        ListCalendarEventsTool,
    )
    from tools.crm import LookupContactTool

    registry = ToolRegistry()
    registry.register(ListCalendarEventsTool(fixtures))
    registry.register(CheckCalendarAvailabilityTool(fixtures))
    registry.register(CreateCalendarEventTool(fixtures))
    registry.register(LookupContactTool(fixtures))
    registry.register(CalculateTool())
    return registry
