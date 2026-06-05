"""coupons & refunds, order discount columns

Revision ID: 002
Revises: 001
Create Date: 2026-06-05

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "coupons",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(50), nullable=False, unique=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("discount_type", sa.String(20), nullable=False),
        sa.Column("discount_value", sa.Integer, nullable=False),
        sa.Column("min_amount", sa.Integer, nullable=False, server_default="0"),
        sa.Column("max_discount", sa.Integer, nullable=False, server_default="0"),
        sa.Column("total_quantity", sa.Integer, nullable=False),
        sa.Column("used_quantity", sa.Integer, nullable=False, server_default="0"),
        sa.Column("valid_from", sa.DateTime, nullable=False),
        sa.Column("valid_until", sa.DateTime, nullable=False),
        sa.Column("status", sa.String(20), server_default="active"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_coupons_code", "coupons", ["code"], unique=True)

    op.add_column("orders", sa.Column("original_amount", sa.Integer, nullable=False, server_default="0"))
    op.add_column("orders", sa.Column("discount_amount", sa.Integer, nullable=False, server_default="0"))
    op.add_column("orders", sa.Column("coupon_id", UUID(as_uuid=True), sa.ForeignKey("coupons.id"), nullable=True))
    op.add_column("orders", sa.Column("coupon_code", sa.String(50), nullable=True))
    # 历史订单原价回填为实付金额
    op.execute("UPDATE orders SET original_amount = amount WHERE original_amount = 0")

    op.create_table(
        "refunds",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("order_id", UUID(as_uuid=True), sa.ForeignKey("orders.id"), nullable=False),
        sa.Column("payment_id", sa.String(100), nullable=False),
        sa.Column("amount", sa.Integer, nullable=False),
        sa.Column("reason", sa.String(200), nullable=False),
        sa.Column("status", sa.String(20), server_default="requested"),
        sa.Column("operator", sa.String(100), nullable=True),
        sa.Column("remark", sa.Text, nullable=True),
        sa.Column("requested_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("processed_at", sa.DateTime, nullable=True),
    )
    op.create_index("ix_refunds_order_status", "refunds", ["order_id", "status"])


def downgrade() -> None:
    op.drop_table("refunds")
    op.drop_column("orders", "coupon_code")
    op.drop_column("orders", "coupon_id")
    op.drop_column("orders", "discount_amount")
    op.drop_column("orders", "original_amount")
    op.drop_index("ix_coupons_code", table_name="coupons")
    op.drop_table("coupons")
