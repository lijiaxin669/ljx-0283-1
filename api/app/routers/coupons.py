from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Session
from app.schemas import CouponValidateIn, CouponValidateOut
from app.services.coupon import get_coupon_by_code, check_usable, compute_discount

router = APIRouter()


@router.post("/validate", response_model=CouponValidateOut)
async def validate_coupon(data: CouponValidateIn, db: AsyncSession = Depends(get_db)):
    """下单前试算优惠券，返回可用性与折扣预览（不核销）。"""
    from sqlalchemy import select

    session = (await db.execute(select(Session).where(Session.id == data.session_id))).scalar_one_or_none()
    if session is None:
        return CouponValidateOut(
            valid=False, code=data.code, original_amount=0,
            discount_amount=0, final_amount=0, message="场次不存在",
        )

    original_amount = session.price
    coupon = await get_coupon_by_code(db, data.code)
    usable, message = check_usable(coupon, original_amount)
    if not usable or coupon is None:
        return CouponValidateOut(
            valid=False, code=data.code, original_amount=original_amount,
            discount_amount=0, final_amount=original_amount, message=message,
        )

    discount = compute_discount(coupon, original_amount)
    return CouponValidateOut(
        valid=True,
        code=coupon.code,
        name=coupon.name,
        original_amount=original_amount,
        discount_amount=discount,
        final_amount=original_amount - discount,
        message=f"已抵扣 ¥{discount / 100:.2f}",
    )
