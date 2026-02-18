"""add workflow_executions table

Revision ID: 7c3e8f1a2b4d
Revises: 0b9b03d3a6aa
Create Date: 2026-02-19 10:00:00

"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7c3e8f1a2b4d"
down_revision: Union[str, Sequence[str], None] = "0b9b03d3a6aa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "workflow_executions",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("workflow_id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=True),
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
            server_default="running",
        ),
        sa.Column("initial_input", sa.Text(), nullable=True),
        sa.Column("model", sa.String(length=255), nullable=True),
        sa.Column(
            "step_outputs_json",
            sa.Text(),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "variables_json",
            sa.Text(),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "executed_nodes_json",
            sa.Text(),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "queue_json",
            sa.Text(),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
        if_not_exists=True,
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_workflow_executions_workflow_id"
        " ON workflow_executions (workflow_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_workflow_executions_user_id"
        " ON workflow_executions (user_id)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_workflow_executions_user_id")
    op.execute("DROP INDEX IF EXISTS ix_workflow_executions_workflow_id")
    op.drop_table("workflow_executions", if_exists=True)
