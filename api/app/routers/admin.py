import csv
import io
import uuid

from fastapi import APIRouter, Depends, HTTPException, Header, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import Order, Session, Payment, Coupon, Refund
from app.schemas import (
    OrderOut, SessionOut, CouponOut, CouponCreate, CouponUpdate,
    RefundDetailOut, RefundApprove, RefundReject,
)
from app.services.refund import approve_refund, reject_refund, RefundError

router = APIRouter()


async def verify_admin(x_admin_secret: str = Header(...)):
    if x_admin_secret != settings.ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="管理端认证失败")
    return True


@router.get("/orders", response_model=list[OrderOut])
async def list_all_orders(
    status: str | None = Query(None),
    _auth: bool = Depends(verify_admin),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Order).order_by(Order.created_at.desc())
    if status:
        stmt = stmt.where(Order.status == status)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/orders/export")
async def export_orders_csv(
    _auth: bool = Depends(verify_admin),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Order, Session, Payment)
        .join(Session, Order.session_id == Session.id)
        .outerjoin(Payment, Payment.order_id == Order.id)
        .order_by(Order.created_at.desc())
    )
    result = await db.execute(stmt)
    rows = result.all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "订单ID", "学员姓名", "学员年龄", "家长姓名", "家长电话",
        "场次", "教练", "开始时间", "结束时间",
        "原价(分)", "优惠码", "优惠金额(分)", "实付金额(分)",
        "订单状态", "支付ID", "支付时间", "创建时间",
    ])
    for order, session, payment in rows:
        writer.writerow([
            str(order.id),
            order.student_name,
            order.student_age,
            order.parent_name,
            order.parent_phone,
            session.title,
            session.coach,
            session.start_time.isoformat(),
            session.end_time.isoformat(),
            order.original_amount,
            order.coupon_code or "",
            order.discount_amount,
            order.amount,
            order.status,
            payment.payment_id if payment else "",
            payment.paid_at.isoformat() if payment and payment.paid_at else "",
            order.created_at.isoformat(),
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=orders.csv"},
    )


@router.get("/sessions", response_model=list[SessionOut])
async def list_all_sessions(
    _auth: bool = Depends(verify_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Session).order_by(Session.start_time))
    return result.scalars().all()


@router.get("/stats")
async def get_stats(
    _auth: bool = Depends(verify_admin),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import func
    total_orders = await db.execute(select(func.count(Order.id)))
    paid_orders = await db.execute(select(func.count(Order.id)).where(Order.status == "paid"))
    pending_orders = await db.execute(select(func.count(Order.id)).where(Order.status == "pending"))
    expired_orders = await db.execute(select(func.count(Order.id)).where(Order.status == "expired"))
    refunded_orders = await db.execute(select(func.count(Order.id)).where(Order.status == "refunded"))
    refunding_orders = await db.execute(select(func.count(Order.id)).where(Order.status == "refunding"))
    total_revenue = await db.execute(select(func.coalesce(func.sum(Order.amount), 0)).where(Order.status == "paid"))
    refunded_amount = await db.execute(select(func.coalesce(func.sum(Order.amount), 0)).where(Order.status == "refunded"))
    total_discount = await db.execute(
        select(func.coalesce(func.sum(Order.discount_amount), 0)).where(Order.status.in_(["paid", "refunded"]))
    )
    pending_refunds = await db.execute(select(func.count(Refund.id)).where(Refund.status == "requested"))

    return {
        "total_orders": total_orders.scalar(),
        "paid_orders": paid_orders.scalar(),
        "pending_orders": pending_orders.scalar(),
        "expired_orders": expired_orders.scalar(),
        "refunded_orders": refunded_orders.scalar(),
        "refunding_orders": refunding_orders.scalar(),
        "total_revenue": total_revenue.scalar(),
        "refunded_amount": refunded_amount.scalar(),
        "total_discount": total_discount.scalar(),
        "pending_refunds": pending_refunds.scalar(),
    }


# ---------------- 优惠券管理 ----------------

@router.get("/coupons", response_model=list[CouponOut])
async def list_coupons(
    _auth: bool = Depends(verify_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Coupon).order_by(Coupon.created_at.desc()))
    return result.scalars().all()


@router.post("/coupons", response_model=CouponOut, status_code=201)
async def create_coupon(
    data: CouponCreate,
    _auth: bool = Depends(verify_admin),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(select(Coupon).where(Coupon.code == data.code))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="优惠码已存在")
    if data.valid_until <= data.valid_from:
        raise HTTPException(status_code=400, detail="失效时间必须晚于生效时间")
    coupon = Coupon(
        code=data.code,
        name=data.name,
        discount_type=data.discount_type,
        discount_value=data.discount_value,
        min_amount=data.min_amount,
        max_discount=data.max_discount,
        total_quantity=data.total_quantity,
        valid_from=data.valid_from,
        valid_until=data.valid_until,
    )
    db.add(coupon)
    await db.commit()
    await db.refresh(coupon)
    return coupon


@router.patch("/coupons/{coupon_id}", response_model=CouponOut)
async def update_coupon(
    coupon_id: uuid.UUID,
    data: CouponUpdate,
    _auth: bool = Depends(verify_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Coupon).where(Coupon.id == coupon_id))
    coupon = result.scalar_one_or_none()
    if coupon is None:
        raise HTTPException(status_code=404, detail="优惠券不存在")
    coupon.status = data.status
    await db.commit()
    await db.refresh(coupon)
    return coupon


# ---------------- 退款管理 ----------------

@router.get("/refunds", response_model=list[RefundDetailOut])
async def list_refunds(
    status: str | None = Query(None),
    _auth: bool = Depends(verify_admin),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Refund, Order, Session)
        .join(Order, Refund.order_id == Order.id)
        .join(Session, Order.session_id == Session.id)
        .order_by(Refund.requested_at.desc())
    )
    if status:
        stmt = stmt.where(Refund.status == status)
    result = await db.execute(stmt)
    rows = result.all()
    return [
        RefundDetailOut(
            id=refund.id,
            order_id=refund.order_id,
            payment_id=refund.payment_id,
            amount=refund.amount,
            reason=refund.reason,
            status=refund.status,
            operator=refund.operator,
            remark=refund.remark,
            requested_at=refund.requested_at,
            processed_at=refund.processed_at,
            student_name=order.student_name,
            session_title=session.title,
        )
        for refund, order, session in rows
    ]


@router.post("/refunds/{refund_id}/approve", response_model=RefundDetailOut)
async def approve_refund_endpoint(
    refund_id: uuid.UUID,
    data: RefundApprove,
    _auth: bool = Depends(verify_admin),
    db: AsyncSession = Depends(get_db),
):
    try:
        refund = await approve_refund(db, refund_id, data.operator, data.remark)
    except RefundError as e:
        await db.rollback()
        raise HTTPException(status_code=e.status_code, detail=e.message)
    await db.commit()
    return await _refund_detail(db, refund.id)


@router.post("/refunds/{refund_id}/reject", response_model=RefundDetailOut)
async def reject_refund_endpoint(
    refund_id: uuid.UUID,
    data: RefundReject,
    _auth: bool = Depends(verify_admin),
    db: AsyncSession = Depends(get_db),
):
    try:
        refund = await reject_refund(db, refund_id, None, data.remark)
    except RefundError as e:
        await db.rollback()
        raise HTTPException(status_code=e.status_code, detail=e.message)
    await db.commit()
    return await _refund_detail(db, refund.id)


async def _refund_detail(db: AsyncSession, refund_id: uuid.UUID) -> RefundDetailOut:
    stmt = (
        select(Refund, Order, Session)
        .join(Order, Refund.order_id == Order.id)
        .join(Session, Order.session_id == Session.id)
        .where(Refund.id == refund_id)
    )
    refund, order, session = (await db.execute(stmt)).first()
    return RefundDetailOut(
        id=refund.id,
        order_id=refund.order_id,
        payment_id=refund.payment_id,
        amount=refund.amount,
        reason=refund.reason,
        status=refund.status,
        operator=refund.operator,
        remark=refund.remark,
        requested_at=refund.requested_at,
        processed_at=refund.processed_at,
        student_name=order.student_name,
        session_title=session.title,
    )
