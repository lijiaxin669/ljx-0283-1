"""initial tables

Revision ID: 001
Revises:
Create Date: 2026-06-05

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sessions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("coach", sa.String(100), nullable=False),
        sa.Column("start_time", sa.DateTime, nullable=False),
        sa.Column("end_time", sa.DateTime, nullable=False),
        sa.Column("total_slots", sa.Integer, nullable=False),
        sa.Column("available_slots", sa.Integer, nullable=False),
        sa.Column("price", sa.Integer, nullable=False),
        sa.Column("status", sa.String(20), server_default="open"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "orders",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("session_id", UUID(as_uuid=True), sa.ForeignKey("sessions.id"), nullable=False),
        sa.Column("student_name", sa.String(100), nullable=False),
        sa.Column("student_age", sa.Integer, nullable=False),
        sa.Column("parent_name", sa.String(100), nullable=False),
        sa.Column("parent_phone", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("amount", sa.Integer, nullable=False),
        sa.Column("expire_at", sa.DateTime, nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_orders_status_expire", "orders", ["status", "expire_at"])

    op.create_table(
        "payments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("order_id", UUID(as_uuid=True), sa.ForeignKey("orders.id"), nullable=False, unique=True),
        sa.Column("payment_id", sa.String(100), nullable=False, unique=True),
        sa.Column("channel", sa.String(50), nullable=False),
        sa.Column("amount", sa.Integer, nullable=False),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("paid_at", sa.DateTime, nullable=True),
        sa.Column("raw_data", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_payments_payment_id", "payments", ["payment_id"], unique=True)


def downgrade() -> None:
    op.drop_table("payments")
    op.drop_table("orders")
    op.drop_table("sessions")
