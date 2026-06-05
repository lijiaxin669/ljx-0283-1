import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Order, Session
from app.schemas import OrderCreate, OrderOut, VoucherOut, RefundCreate, RefundOut
from app.services.inventory import create_order, OrderError
from app.services.refund import request_refund, RefundError

router = APIRouter()


@router.post("", response_model=OrderOut, status_code=201)
async def place_order(data: OrderCreate, db: AsyncSession = Depends(get_db)):
    try:
        order = await create_order(
            db=db,
            session_id=data.session_id,
            student_name=data.student_name,
            student_age=data.student_age,
            parent_name=data.parent_name,
            parent_phone=data.parent_phone,
            coupon_code=data.coupon_code,
        )
    except OrderError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=e.message)
    if order is None:
        await db.rollback()
        raise HTTPException(status_code=409, detail="库存不足或场次已关闭")
    await db.commit()
    await db.refresh(order)
    return order


@router.post("/{order_id}/refund", response_model=RefundOut, status_code=201)
async def apply_refund(order_id: uuid.UUID, data: RefundCreate, db: AsyncSession = Depends(get_db)):
    try:
        refund = await request_refund(db, order_id, data.reason)
    except RefundError as e:
        await db.rollback()
        raise HTTPException(status_code=e.status_code, detail=e.message)
    await db.commit()
    await db.refresh(refund)
    return refund


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
        original_amount=order.original_amount,
        discount_amount=order.discount_amount,
        coupon_code=order.coupon_code,
        payment_id=payment.payment_id,
        paid_at=payment.paid_at,
    )
