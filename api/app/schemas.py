import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class SessionOut(BaseModel):
    id: uuid.UUID
    title: str
    description: str | None
    coach: str
    start_time: datetime
    end_time: datetime
    total_slots: int
    available_slots: int
    price: int
    status: str

    model_config = {"from_attributes": True}


class SessionCreate(BaseModel):
    title: str = Field(..., max_length=200)
    description: str | None = None
    coach: str = Field(..., max_length=100)
    start_time: datetime
    end_time: datetime
    total_slots: int = Field(..., gt=0)
    price: int = Field(..., gt=0)


class SessionUpdate(BaseModel):
    title: str | None = Field(None, max_length=200)
    description: str | None = None
    coach: str | None = Field(None, max_length=100)
    start_time: datetime | None = None
    end_time: datetime | None = None
    price: int | None = Field(None, gt=0)


class SessionSlotsUpdate(BaseModel):
    total_slots: int = Field(..., gt=0)


class SessionStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(open|closed|full)$")


class SessionDetailOut(BaseModel):
    id: uuid.UUID
    title: str
    description: str | None
    coach: str
    start_time: datetime
    end_time: datetime
    total_slots: int
    available_slots: int
    price: int
    status: str
    booked_count: int
    pending_count: int
    paid_amount: int

    model_config = {"from_attributes": True}


class OrderCreate(BaseModel):
    session_id: uuid.UUID
    student_name: str = Field(..., max_length=100)
    student_age: int = Field(..., ge=1, le=18)
    parent_name: str = Field(..., max_length=100)
    parent_phone: str = Field(..., max_length=20)
    coupon_code: str | None = Field(None, max_length=50)


class OrderOut(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    student_name: str
    student_age: int
    parent_name: str
    parent_phone: str
    status: str
    amount: int
    original_amount: int
    discount_amount: int
    coupon_code: str | None
    expire_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class PaymentCreate(BaseModel):
    order_id: uuid.UUID
    channel: str = Field(..., max_length=50)


class PaymentCallback(BaseModel):
    payment_id: str = Field(..., max_length=100)
    order_id: uuid.UUID
    channel: str = Field(..., max_length=50)
    amount: int
    status: str
    raw_data: str | None = None


class PaymentOut(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    payment_id: str
    channel: str
    amount: int
    status: str
    paid_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class VoucherOut(BaseModel):
    order_id: uuid.UUID
    student_name: str
    student_age: int
    parent_name: str
    parent_phone: str
    session_title: str
    coach: str
    start_time: datetime
    end_time: datetime
    amount: int
    original_amount: int
    discount_amount: int
    coupon_code: str | None
    payment_id: str
    paid_at: datetime


# ---------------- 优惠券 ----------------

class CouponCreate(BaseModel):
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=100)
    discount_type: str = Field(..., pattern="^(fixed|percent)$")
    discount_value: int = Field(..., gt=0)
    min_amount: int = Field(0, ge=0)
    max_discount: int = Field(0, ge=0)
    total_quantity: int = Field(..., gt=0)
    valid_from: datetime
    valid_until: datetime


class CouponOut(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    discount_type: str
    discount_value: int
    min_amount: int
    max_discount: int
    total_quantity: int
    used_quantity: int
    valid_from: datetime
    valid_until: datetime
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class CouponUpdate(BaseModel):
    status: str = Field(..., pattern="^(active|disabled)$")


class CouponValidateIn(BaseModel):
    code: str = Field(..., max_length=50)
    session_id: uuid.UUID


class CouponValidateOut(BaseModel):
    valid: bool
    code: str
    name: str | None = None
    original_amount: int
    discount_amount: int
    final_amount: int
    message: str


# ---------------- 退款 ----------------

class RefundCreate(BaseModel):
    reason: str = Field(..., max_length=200)


class RefundReject(BaseModel):
    remark: str | None = Field(None, max_length=500)


class RefundApprove(BaseModel):
    operator: str | None = Field(None, max_length=100)
    remark: str | None = Field(None, max_length=500)


class RefundOut(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    payment_id: str
    amount: int
    reason: str
    status: str
    operator: str | None
    remark: str | None
    requested_at: datetime
    processed_at: datetime | None

    model_config = {"from_attributes": True}


class RefundDetailOut(RefundOut):
    student_name: str
    session_title: str
