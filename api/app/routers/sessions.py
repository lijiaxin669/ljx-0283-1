import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Session
from app.schemas import SessionOut, SessionCreate

router = APIRouter()


@router.get("", response_model=list[SessionOut])
async def list_sessions(
    date_filter: date | None = Query(None, description="按日期筛选，格式 YYYY-MM-DD"),
    coach: str | None = Query(None, description="按教练筛选"),
    status: str | None = Query(None, description="按状态筛选: open/closed/full"),
    sort_by: str | None = Query(None, description="排序字段: start_time/price/available_slots"),
    sort_order: str | None = Query("asc", description="排序方向: asc/desc"),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Session)

    if date_filter:
        stmt = stmt.where(cast(Session.start_time, Date) == date_filter)

    if coach:
        stmt = stmt.where(Session.coach == coach)

    if status:
        stmt = stmt.where(Session.status == status)

    order_column = Session.start_time
    if sort_by == "price":
        order_column = Session.price
    elif sort_by == "available_slots":
        order_column = Session.available_slots

    if sort_order == "desc":
        stmt = stmt.order_by(order_column.desc())
    else:
        stmt = stmt.order_by(order_column.asc())

    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/coaches", response_model=list[str])
async def list_coaches(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Session.coach).distinct().order_by(Session.coach))
    return [row for row in result.scalars().all()]


@router.get("/{session_id}", response_model=SessionOut)
async def get_session(session_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=404, detail="场次不存在")
    return session


@router.post("", response_model=SessionOut, status_code=201)
async def create_session(data: SessionCreate, db: AsyncSession = Depends(get_db)):
    session = Session(
        title=data.title,
        description=data.description,
        coach=data.coach,
        start_time=data.start_time,
        end_time=data.end_time,
        total_slots=data.total_slots,
        available_slots=data.total_slots,
        price=data.price,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session
