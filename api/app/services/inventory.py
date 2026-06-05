import uuid
from datetime import datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Session, Order, Payment


async def lock_and_decrease_inventory(db: AsyncSession, session_id: uuid.UUID) -> Session | None:
    stmt = select(Session).where(Session.id == session_id).with_for_update()
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()
    if session is None or session.available_slots <= 0 or session.status != "open":
        return None
    session.available_slots -= 1
    if session.available_slots == 0:
        session.status = "full"
    await db.flush()
    return session


async def restore_inventory(db: AsyncSession, session_id: uuid.UUID, count: int = 1) -> None:
    stmt = select(Session).where(Session.id == session_id).with_for_update()
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()
    if session is None:
        return
    session.available_slots += count
    if session.status == "full" and session.available_slots > 0:
        session.status = "open"
    await db.flush()


async def create_order(db: AsyncSession, session_id: uuid.UUID, student_name: str, student_age: int, parent_name: str, parent_phone: str) -> Order | None:
    session = await lock_and_decrease_inventory(db, session_id)
    if session is None:
        return None
    expire_at = datetime.utcnow() + timedelta(minutes=settings.ORDER_EXPIRE_MINUTES)
    order = Order(
        session_id=session_id,
        student_name=student_name,
        student_age=student_age,
        parent_name=parent_name,
        parent_phone=parent_phone,
        status="pending",
        amount=session.price,
        expire_at=expire_at,
    )
    db.add(order)
    await db.flush()
    await db.refresh(order)
    return order


async def release_expired_orders(db: AsyncSession) -> int:
    now = datetime.utcnow()
    stmt = select(Order).where(Order.status == "pending", Order.expire_at < now)
    result = await db.execute(stmt)
    expired_orders = result.scalars().all()
    count = 0
    for order in expired_orders:
        order.status = "expired"
        await restore_inventory(db, order.session_id)
        count += 1
    await db.flush()
    return count


async def confirm_payment(db: AsyncSession, payment_id: str, order_id: uuid.UUID, channel: str, amount: int, raw_data: str | None = None) -> Payment | None:
    existing = await db.execute(select(Payment).where(Payment.payment_id == payment_id))
    payment = existing.scalar_one_or_none()
    if payment is not None:
        return payment

    order_stmt = select(Order).where(Order.id == order_id).with_for_update()
    order_result = await db.execute(order_stmt)
    order = order_result.scalar_one_or_none()
    if order is None or order.status != "pending":
        return None
    if datetime.utcnow() > order.expire_at:
        order.status = "expired"
        await restore_inventory(db, order.session_id)
        await db.flush()
        return None

    payment = Payment(
        order_id=order_id,
        payment_id=payment_id,
        channel=channel,
        amount=amount,
        status="paid",
        paid_at=datetime.utcnow(),
        raw_data=raw_data,
    )
    db.add(payment)
    order.status = "paid"
    await db.flush()
    await db.refresh(payment)
    return payment
