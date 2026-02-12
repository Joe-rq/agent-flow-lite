"""
Workflow execution context and expression helpers.
"""
from __future__ import annotations

from typing import Any, Dict
import re

InvalidExpression: type[Exception]


class _MissingInvalidExpression(Exception):
    pass

try:
    from simpleeval import InvalidExpression, simple_eval
except ImportError:
    InvalidExpression = _MissingInvalidExpression
    simple_eval = None


# Support node IDs with hyphens (UUIDs like beddf374-3de6-4aba-bd0e-03a49b5baac7)
TEMPLATE_PATTERN = re.compile(r"\{\{([\w-]+(?:\.[\w-]+)*)\}\}")


class ExecutionContext:
    """Execution context for variables and node outputs."""

    def __init__(self, initial_input: str):
        self.variables: Dict[str, Any] = {"input": initial_input}
        self.step_outputs: Dict[str, Any] = {}

    def set_output(self, node_id: str, value: Any) -> None:
        self.step_outputs[node_id] = value
        self.variables[f"{node_id}.output"] = value

    def get_variable(self, var_path: str) -> Any:
        # First try flat key lookup (e.g. "node-id.output" stored by set_output)
        if var_path in self.variables:
            return self.variables[var_path]
        # Fallback to nested path traversal
        current: Any = self.variables
        for part in var_path.split("."):
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None
        return current

    def resolve_template(self, template: str) -> str:
        def replace_var(match: re.Match[str]) -> str:
            value = self.get_variable(match.group(1))
            return str(value) if value is not None else match.group(0)

        return TEMPLATE_PATTERN.sub(replace_var, template)

    def resolve_expression(self, expression: str) -> str:
        def replace_var(match: re.Match[str]) -> str:
            value = self.get_variable(match.group(1))
            if value is None:
                return match.group(0)
            return repr(value)

        return TEMPLATE_PATTERN.sub(replace_var, expression)


def normalize_expression(expression: str) -> str:
    """Normalize JS-style operators to Python, preserving string literals."""
    expr = expression.strip()
    expr = expr.replace("===", "==").replace("!==", "!=")
    expr = expr.replace("&&", " and ").replace("||", " or ")

    # Only replace true/false/contains OUTSIDE of string literals
    # Split by quoted strings, only transform non-string parts
    parts = re.split(r'("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\')', expr)
    for i, part in enumerate(parts):
        if i % 2 == 0:  # Not inside a string literal
            part = re.sub(r"\btrue\b", "True", part, flags=re.IGNORECASE)
            part = re.sub(r"\bfalse\b", "False", part, flags=re.IGNORECASE)
            parts[i] = part
    return "".join(parts)


_SAFE_NAMES: Dict[str, Any] = {"None": None, "True": True, "False": False}


def _rewrite_contains(expression: str) -> str:
    in_single = False
    in_double = False
    i = 0
    lower = expression.lower()

    while i < len(expression):
        ch = expression[i]
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double

        if not in_single and not in_double and lower.startswith("contains", i):
            prev_ok = i == 0 or not expression[i - 1].isalnum()
            next_idx = i + 8
            next_ok = next_idx >= len(expression) or not expression[next_idx].isalnum()
            if prev_ok and next_ok:
                left = expression[:i].strip()
                right = expression[next_idx:].strip()
                if left and right:
                    return f"({right}) in ({left})"
        i += 1

    return expression


def safe_eval(expression: str) -> bool:
    expr = normalize_expression(expression)
    expr = _rewrite_contains(expr)
    if simple_eval is None:
        import logging
        logging.warning(
            f"simpleeval not available, falling back to string comparison for: {expr}"
        )
        lowered = expr.lower()
        return lowered in ("true", "yes", "1")

    try:
        return bool(simple_eval(expr, names=_SAFE_NAMES, functions={}))

    except (TypeError, ValueError, NameError, InvalidExpression):
        import logging
        logging.warning(f"Expression evaluation error in {expr}")
        return False

    except Exception as e:
        import logging
        logging.error(f"Unexpected error in safe_eval({expr}): {e}")
        raise
