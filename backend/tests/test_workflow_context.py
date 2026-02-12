from app.core.workflow.workflow_context import ExecutionContext, normalize_expression, safe_eval


def test_resolve_expression_supports_hyphenated_node_id() -> None:
    ctx = ExecutionContext('input')
    ctx.set_output('node-1', 'yes')

    resolved = ctx.resolve_expression("{{node-1.output}} == 'yes'")

    assert safe_eval(resolved) is True


def test_contains_operator_compatibility() -> None:
    ctx = ExecutionContext('input')
    ctx.set_output('step-1', 'project risk summary')

    resolved = ctx.resolve_expression("{{step-1.output}} contains 'risk'")

    assert safe_eval(resolved) is True


def test_contains_literal_not_rewritten_inside_string() -> None:
    normalized = normalize_expression("'contains' == 'contains'")

    assert normalized == "'contains' == 'contains'"
    assert safe_eval(normalized) is True
