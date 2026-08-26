"""Migrate llm_executions.steps JSON column to relational llm_execution_steps table.

Revision ID: f8a9b2c3d4e5
Revises: f2858749267a
Create Date: 2026-08-26
"""

import json
from datetime import datetime, timezone
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql, sqlite

# Revision identifiers, used by Alembic.
revision = "f8a9b2c3d4e5"
down_revision = "f2858749267a"
branch_labels = None
depends_on = None


def parse_to_datetime(val) -> datetime:
    """Helper to convert string or existing datetime into a valid timezone-aware datetime object."""
    if isinstance(val, datetime):
        return val
    if isinstance(val, str):
        try:
            return datetime.fromisoformat(val)
        except ValueError:
            pass
    return datetime.now(timezone.utc)


def upgrade() -> None:
    # 1. Create the new llm_execution_steps table
    op.create_table(
        "llm_execution_steps",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("execution_id", sa.String(length=36), nullable=False),
        sa.Column("step_number", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("tool_name", sa.String(length=255), nullable=True),
        sa.Column("parameters", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("result", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["execution_id"], ["llm_executions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_llm_execution_steps_execution_id"),
        "llm_execution_steps",
        ["execution_id"],
        unique=False,
    )

    # 2. Data Migration: Extract legacy JSON array steps into llm_execution_steps
    connection = op.get_bind()
    executions = connection.execute(
        sa.text("SELECT id, steps, created_at FROM llm_executions WHERE steps IS NOT NULL")
    ).fetchall()

    steps_to_insert = []
    now_dt = datetime.now(timezone.utc)

    for exec_id, raw_steps, created_at in executions:
        if not raw_steps:
            continue

        parsed_steps = raw_steps
        if isinstance(raw_steps, str):
            try:
                parsed_steps = json.loads(raw_steps)
            except Exception:
                continue

        if isinstance(parsed_steps, list):
            # Parse row datetime once per execution
            exec_dt = parse_to_datetime(created_at) if created_at else now_dt

            for step in parsed_steps:
                if not isinstance(step, dict):
                    continue

                step_num = step.get("step") or step.get("step_number")
                if step_num is None:
                    continue

                tool_val = step.get("tool") or step.get("tool_name")
                params_val = step.get("parameters") if isinstance(step.get("parameters"), dict) else {}
                status_val = step.get("status") or "PENDING"
                if isinstance(status_val, str):
                    status_val = status_val.upper()

                steps_to_insert.append({
                    "id": str(uuid.uuid4()),
                    "execution_id": str(exec_id),
                    "step_number": int(step_num),
                    "description": str(step.get("description", "")),
                    "tool_name": str(tool_val) if tool_val else None,
                    "parameters": json.dumps(params_val),
                    "status": status_val,
                    "result": str(step.get("result")) if step.get("result") is not None else None,
                    "created_at": exec_dt,
                    "updated_at": exec_dt,
                })

    if steps_to_insert:
        op.bulk_insert(
            sa.table(
                "llm_execution_steps",
                sa.column("id", sa.String),
                sa.column("execution_id", sa.String),
                sa.column("step_number", sa.Integer),
                sa.column("description", sa.Text),
                sa.column("tool_name", sa.String),
                sa.column("parameters", sa.JSON),
                sa.column("status", sa.String),
                sa.column("result", sa.Text),
                sa.column("created_at", sa.DateTime),
                sa.column("updated_at", sa.DateTime),
            ),
            steps_to_insert,
        )

    # 3. Drop legacy steps JSON column from llm_executions
    with op.batch_alter_table("llm_executions", schema=None) as batch_op:
        batch_op.drop_column("steps")


def downgrade() -> None:
    # 1. Re-add steps JSON column to llm_executions
    with op.batch_alter_table("llm_executions", schema=None) as batch_op:
        batch_op.add_column(sa.Column("steps", sa.JSON(), nullable=True))

    # 2. Reverse Data Migration: Reconstruct JSON array in llm_executions
    connection = op.get_bind()
    steps_rows = connection.execute(
        sa.text(
            "SELECT execution_id, step_number, description, tool_name, parameters, status, result "
            "FROM llm_execution_steps ORDER BY execution_id, step_number"
        )
    ).fetchall()

    grouped_steps = {}
    for exec_id, step_num, desc, tool, params, status, result in steps_rows:
        if exec_id not in grouped_steps:
            grouped_steps[exec_id] = []

        parsed_params = params
        if isinstance(params, str):
            try:
                parsed_params = json.loads(params)
            except Exception:
                parsed_params = {}

        grouped_steps[exec_id].append({
            "step": step_num,
            "description": desc,
            "tool": tool,
            "parameters": parsed_params,
            "status": status.lower() if isinstance(status, str) else "pending",
            "result": result,
        })

    for exec_id, steps_list in grouped_steps.items():
        connection.execute(
            sa.text("UPDATE llm_executions SET steps = :steps WHERE id = :id"),
            {"steps": json.dumps(steps_list), "id": exec_id},
        )

    # Set empty array for executions without steps to prevent NULLs
    connection.execute(sa.text("UPDATE llm_executions SET steps = '[]' WHERE steps IS NULL"))

    # 3. Drop llm_execution_steps table
    op.drop_index(op.f("ix_llm_execution_steps_execution_id"), table_name="llm_execution_steps")
    op.drop_table("llm_execution_steps")