import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Payment
from app.schemas import PaymentCreate, PaymentCallback, PaymentOut
from app.services.inventory import confirm_payment

router = APIRouter()


@router.post("/create", response_model=PaymentOut)
async def create_payment(data: PaymentCreate, db: AsyncSession = Depends(get_db)):
    from app.models import Order
    order_result = await db.execute(select(Order).where(Order.id == data.order_id))
    order = order_result.scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.status != "pending":
        raise HTTPException(status_code=400, detail="订单状态不可支付")

    import time
    payment_id = f"PAY-{int(time.time() * 1000)}-{uuid.uuid4().hex[:8]}"
    payment = Payment(
        order_id=data.order_id,
        payment_id=payment_id,
        channel=data.channel,
        amount=order.amount,
        status="pending",
    )
    db.add(payment)
    await db.commit()
    await db.refresh(payment)
    return payment


@router.post("/callback", response_model=PaymentOut)
async def payment_callback(data: PaymentCallback, db: AsyncSession = Depends(get_db)):
    payment = await confirm_payment(
        db=db,
        payment_id=data.payment_id,
        order_id=data.order_id,
        channel=data.channel,
        amount=data.amount,
        raw_data=data.raw_data,
    )
    if payment is None:
        raise HTTPException(status_code=400, detail="订单已过期或状态异常")
    await db.commit()
    await db.refresh(payment)
    return payment


@router.get("/{payment_id}", response_model=PaymentOut)
async def get_payment(payment_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Payment).where(Payment.payment_id == payment_id))
    payment = result.scalar_one_or_none()
    if payment is None:
        raise HTTPException(status_code=404, detail="支付记录不存在")
    return payment
