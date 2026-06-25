"""Safe calculator and unit conversion tool."""

from __future__ import annotations

import ast
import operator
import re
from typing import Any

from tools.base import BaseTool, ToolResult

_SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

_UNIT_PATTERNS = [
    (re.compile(r"^(\d+(?:\.\d+)?)\s*miles?\s+to\s+(?:km|kilometers?)$", re.I), lambda v: v * 1.60934, "km"),
    (re.compile(r"^(\d+(?:\.\d+)?)\s*km\s+to\s+miles?$", re.I), lambda v: v / 1.60934, "miles"),
    (re.compile(r"^(\d+(?:\.\d+)?)\s*hours?\s+to\s+minutes?$", re.I), lambda v: v * 60, "minutes"),
    (re.compile(r"^(\d+(?:\.\d+)?)\s*minutes?\s+to\s+hours?$", re.I), lambda v: v / 60, "hours"),
]

_TIME_RANGE_PATTERN = re.compile(
    r"minutes?\s+between\s+(\d{1,2}):(\d{2})\s+and\s+(\d{1,2}):(\d{2})",
    re.I,
)


def _safe_eval(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _safe_eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.BinOp):
        op = _SAFE_OPERATORS.get(type(node.op))
        if op is None:
            raise ValueError("Unsupported operator")
        return op(_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp):
        op = _SAFE_OPERATORS.get(type(node.op))
        if op is None:
            raise ValueError("Unsupported operator")
        return op(_safe_eval(node.operand))
    raise ValueError("Unsupported expression")


def _try_unit_conversion(expression: str) -> tuple[float, str] | None:
    expr = expression.strip()
    for pattern, convert, unit in _UNIT_PATTERNS:
        match = pattern.match(expr)
        if match:
            value = float(match.group(1))
            return convert(value), unit
    return None


def _try_time_difference(expression: str) -> float | None:
    match = _TIME_RANGE_PATTERN.search(expression)
    if not match:
        return None
    h1, m1, h2, m2 = (int(match.group(i)) for i in range(1, 5))
    start = h1 * 60 + m1
    end = h2 * 60 + m2
    if end < start:
        end += 24 * 60
    return float(end - start)


class CalculateTool(BaseTool):
    name = "calculate"
    description = (
        "Evaluate a mathematical expression or unit conversion. Use for arithmetic, "
        "time differences, miles/km, hours/minutes, etc. "
        "Do NOT use for calendar, scheduling, or looking up people/contacts."
    )
    parameters = {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": (
                    "Math expression (e.g. '8.5 * 60') or conversion "
                    "(e.g. '50 miles to km', 'minutes between 9:00 and 17:30')."
                ),
            },
        },
        "required": ["expression"],
    }

    def run(self, **kwargs: Any) -> ToolResult:
        expression = kwargs["expression"].strip()

        time_diff = _try_time_difference(expression)
        if time_diff is not None:
            return ToolResult(
                success=True,
                data={"result": time_diff, "unit": "minutes", "expression": expression},
            )

        unit_result = _try_unit_conversion(expression)
        if unit_result is not None:
            value, unit = unit_result
            return ToolResult(
                success=True,
                data={"result": round(value, 4), "unit": unit, "expression": expression},
            )

        try:
            tree = ast.parse(expression, mode="eval")
            result = _safe_eval(tree)
            return ToolResult(
                success=True,
                data={"result": result, "expression": expression},
            )
        except (SyntaxError, ValueError, TypeError, ZeroDivisionError) as exc:
            return ToolResult(
                success=False,
                error=f"Could not evaluate expression: {exc}",
                code="VALIDATION_ERROR",
            )
