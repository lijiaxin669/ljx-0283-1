import csv
import io
import uuid

from fastapi import APIRouter, Depends, HTTPException, Header, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import Order, Session, Payment
from app.schemas import OrderOut, SessionOut

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
        "金额(分)", "订单状态", "支付ID", "支付时间", "创建时间",
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
    total_revenue = await db.execute(select(func.coalesce(func.sum(Order.amount), 0)).where(Order.status == "paid"))

    return {
        "total_orders": total_orders.scalar(),
        "paid_orders": paid_orders.scalar(),
        "pending_orders": pending_orders.scalar(),
        "expired_orders": expired_orders.scalar(),
        "total_revenue": total_revenue.scalar(),
    }
