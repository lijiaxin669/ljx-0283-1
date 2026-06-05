"""退款服务。

退款状态机：
    requested 待审核 ──approve──▶ refunded 已退款（释放名额/优惠券）
                     └─reject──▶ rejected 已驳回（订单恢复 paid）

订单状态：paid ──申请──▶ refunding ──审批──▶ refunded / paid
对订单、退款单加行级锁，审批操作具备幂等性（重复审批返回已有结果）。
"""
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Order, Payment, Refund
from app.services.coupon import release_coupon
from app.services.inventory import restore_inventory


class RefundError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


async def request_refund(db: AsyncSession, order_id: uuid.UUID, reason: str) -> Refund:
    order_stmt = select(Order).where(Order.id == order_id).with_for_update()
    order = (await db.execute(order_stmt)).scalar_one_or_none()
    if order is None:
        raise RefundError("订单不存在", 404)
    if order.status == "refunding":
        raise RefundError("已存在待处理的退款申请")
    if order.status == "refunded":
        raise RefundError("订单已退款")
    if order.status != "paid":
        raise RefundError("仅已支付订单可申请退款")

    payment_stmt = select(Payment).where(Payment.order_id == order_id)
    payment = (await db.execute(payment_stmt)).scalar_one_or_none()
    if payment is None:
        raise RefundError("支付记录不存在", 404)

    refund = Refund(
        order_id=order_id,
        payment_id=payment.payment_id,
        amount=order.amount,
        reason=reason,
        status="requested",
    )
    order.status = "refunding"
    db.add(refund)
    await db.flush()
    await db.refresh(refund)
    return refund


async def _get_refund_locked(db: AsyncSession, refund_id: uuid.UUID) -> Refund:
    stmt = select(Refund).where(Refund.id == refund_id).with_for_update()
    refund = (await db.execute(stmt)).scalar_one_or_none()
    if refund is None:
        raise RefundError("退款单不存在", 404)
    return refund


async def approve_refund(db: AsyncSession, refund_id: uuid.UUID, operator: str | None, remark: str | None) -> Refund:
    refund = await _get_refund_locked(db, refund_id)
    if refund.status == "refunded":
        return refund  # 幂等：已退款直接返回
    if refund.status != "requested":
        raise RefundError("退款单状态不可审批")

    order_stmt = select(Order).where(Order.id == refund.order_id).with_for_update()
    order = (await db.execute(order_stmt)).scalar_one_or_none()
    if order is None:
        raise RefundError("订单不存在", 404)

    payment_stmt = select(Payment).where(Payment.order_id == refund.order_id).with_for_update()
    payment = (await db.execute(payment_stmt)).scalar_one_or_none()
    if payment is not None and payment.status != "refunded":
        payment.status = "refunded"

    order.status = "refunded"
    await restore_inventory(db, order.session_id)
    await release_coupon(db, order.coupon_id)

    refund.status = "refunded"
    refund.operator = operator
    refund.remark = remark
    refund.processed_at = datetime.utcnow()
    await db.flush()
    await db.refresh(refund)
    return refund


async def reject_refund(db: AsyncSession, refund_id: uuid.UUID, operator: str | None, remark: str | None) -> Refund:
    refund = await _get_refund_locked(db, refund_id)
    if refund.status == "rejected":
        return refund  # 幂等
    if refund.status != "requested":
        raise RefundError("退款单状态不可驳回")

    order_stmt = select(Order).where(Order.id == refund.order_id).with_for_update()
    order = (await db.execute(order_stmt)).scalar_one_or_none()
    if order is not None and order.status == "refunding":
        order.status = "paid"

    refund.status = "rejected"
    refund.operator = operator
    refund.remark = remark
    refund.processed_at = datetime.utcnow()
    await db.flush()
    await db.refresh(refund)
    return refund
