import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Order, Session
from app.schemas import OrderCreate, OrderOut, VoucherOut
from app.services.inventory import create_order

router = APIRouter()


@router.post("", response_model=OrderOut, status_code=201)
async def place_order(data: OrderCreate, db: AsyncSession = Depends(get_db)):
    order = await create_order(
        db=db,
        session_id=data.session_id,
        student_name=data.student_name,
        student_age=data.student_age,
        parent_name=data.parent_name,
        parent_phone=data.parent_phone,
    )
    if order is None:
        raise HTTPException(status_code=409, detail="库存不足或场次已关闭")
    await db.commit()
    await db.refresh(order)
    return order


@router.get("/{order_id}", response_model=OrderOut)
async def get_order(order_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail="订单不存在")
    return order


@router.get("/{order_id}/voucher", response_model=VoucherOut)
async def get_voucher(order_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    stmt = select(Order, Session).join(Session, Order.session_id == Session.id).where(Order.id == order_id, Order.status == "paid")
    result = await db.execute(stmt)
    row = result.first()
    if row is None:
        raise HTTPException(status_code=404, detail="凭证不存在或订单未支付")
    order, session = row
    payment_result = await db.execute(select(Order).where(Order.id == order_id))
    payment_stmt = select(Session).where(Session.id == session.id)

    from app.models import Payment
    pay_result = await db.execute(select(Payment).where(Payment.order_id == order_id))
    payment = pay_result.scalar_one_or_none()
    if payment is None:
        raise HTTPException(status_code=404, detail="支付记录不存在")

    return VoucherOut(
        order_id=order.id,
        student_name=order.student_name,
        student_age=order.student_age,
        parent_name=order.parent_name,
        parent_phone=order.parent_phone,
        session_title=session.title,
        coach=session.coach,
        start_time=session.start_time,
        end_time=session.end_time,
        amount=order.amount,
        payment_id=payment.payment_id,
        paid_at=payment.paid_at,
    )
