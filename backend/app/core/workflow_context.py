"""
Workflow execution context and expression helpers.
"""
from __future__ import annotations

from typing import Any, Dict
import re


TEMPLATE_PATTERN = re.compile(r"\{\{(\w+(?:\.\w+)*)\}\}")


class ExecutionContext:
    """Execution context for variables and node outputs."""

    def __init__(self, initial_input: str):
        self.variables: Dict[str, Any] = {"input": initial_input}
        self.step_outputs: Dict[str, Any] = {}

    def set_output(self, node_id: str, value: Any) -> None:
        self.step_outputs[node_id] = value
        self.variables[f"{node_id}.output"] = value

    def get_variable(self, var_path: str) -> Any:
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
            return repr(value)

        return TEMPLATE_PATTERN.sub(replace_var, expression)


def normalize_expression(expression: str) -> str:
    expr = expression.strip()
    expr = expr.replace("===", "==").replace("!==", "!=")
    expr = expr.replace("&&", " and ").replace("||", " or ")
    expr = re.sub(r"\btrue\b", "True", expr, flags=re.IGNORECASE)
    expr = re.sub(r"\bfalse\b", "False", expr, flags=re.IGNORECASE)
    expr = re.sub(r"\bcontains\b", "in", expr, flags=re.IGNORECASE)
    return expr


def safe_eval(expression: str) -> bool:
    expr = normalize_expression(expression)
    try:
        from simpleeval import simple_eval, InvalidExpression

        # Explicit empty whitelists - no implicit imports or function calls
        return bool(simple_eval(expr, names={}, functions={}))

    except ImportError:
        import logging
        logging.warning(
            f"simpleeval not available, falling back to string comparison for: {expr}"
        )
        lowered = expr.lower()
        # Fallback contract: only boolean literal values are True
        return lowered in ("true", "yes", "1")

    except (TypeError, ValueError, NameError, InvalidExpression):
        import logging
        logging.warning(f"Expression evaluation error in {expr}")
        return False

    except Exception as e:
        import logging
        logging.error(f"Unexpected error in safe_eval({expr}): {e}")
        raise
