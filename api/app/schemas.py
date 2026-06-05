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


class OrderCreate(BaseModel):
    session_id: uuid.UUID
    student_name: str = Field(..., max_length=100)
    student_age: int = Field(..., ge=1, le=18)
    parent_name: str = Field(..., max_length=100)
    parent_phone: str = Field(..., max_length=20)


class OrderOut(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    student_name: str
    student_age: int
    parent_name: str
    parent_phone: str
    status: str
    amount: int
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
    payment_id: str
    paid_at: datetime
