"""优惠券核销与折扣计算服务。

折扣规则：
- fixed   固定立减：discount = min(discount_value, amount)
- percent 百分比立减：discount = floor(amount * discount_value / 100)，
          若 max_discount > 0 则再封顶到 max_discount

下单时对优惠券行加锁（with_for_update）并自增 used_quantity，防止超发；
订单过期或退款时调用 release_coupon 归还使用次数。
"""
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Coupon


def compute_discount(coupon: Coupon, amount: int) -> int:
    """根据优惠券与原价计算立减金额（分），不做有效性校验。"""
    if amount < coupon.min_amount:
        return 0
    if coupon.discount_type == "fixed":
        discount = min(coupon.discount_value, amount)
    elif coupon.discount_type == "percent":
        discount = amount * coupon.discount_value // 100
        if coupon.max_discount > 0:
            discount = min(discount, coupon.max_discount)
    else:
        discount = 0
    return max(0, min(discount, amount))


def check_usable(coupon: Coupon | None, amount: int, now: datetime | None = None) -> tuple[bool, str]:
    """校验优惠券是否可用，返回 (是否可用, 提示信息)。"""
    now = now or datetime.utcnow()
    if coupon is None:
        return False, "优惠券不存在"
    if coupon.status != "active":
        return False, "优惠券已停用"
    if now < coupon.valid_from:
        return False, "优惠券尚未生效"
    if now > coupon.valid_until:
        return False, "优惠券已过期"
    if coupon.used_quantity >= coupon.total_quantity:
        return False, "优惠券已被领完"
    if amount < coupon.min_amount:
        yuan = coupon.min_amount / 100
        return False, f"订单金额需满 ¥{yuan:.2f} 方可使用"
    if compute_discount(coupon, amount) <= 0:
        return False, "该优惠券对此订单无优惠"
    return True, "可用"


async def get_coupon_by_code(db: AsyncSession, code: str, lock: bool = False) -> Coupon | None:
    stmt = select(Coupon).where(Coupon.code == code)
    if lock:
        stmt = stmt.with_for_update()
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def redeem_coupon(db: AsyncSession, code: str, amount: int) -> tuple[Coupon | None, int, str]:
    """锁定并核销优惠券，自增 used_quantity。

    返回 (coupon, discount, message)。若不可用则 coupon 为 None、discount 为 0。
    """
    coupon = await get_coupon_by_code(db, code, lock=True)
    usable, message = check_usable(coupon, amount)
    if not usable or coupon is None:
        return None, 0, message
    discount = compute_discount(coupon, amount)
    coupon.used_quantity += 1
    await db.flush()
    return coupon, discount, "核销成功"


async def release_coupon(db: AsyncSession, coupon_id: uuid.UUID | None) -> None:
    """归还优惠券使用次数（订单过期/退款时调用）。"""
    if coupon_id is None:
        return
    stmt = select(Coupon).where(Coupon.id == coupon_id).with_for_update()
    result = await db.execute(stmt)
    coupon = result.scalar_one_or_none()
    if coupon is None:
        return
    if coupon.used_quantity > 0:
        coupon.used_quantity -= 1
    await db.flush()
