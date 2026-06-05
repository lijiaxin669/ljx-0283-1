import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Session
from app.schemas import SessionOut, SessionCreate

router = APIRouter()


@router.get("", response_model=list[SessionOut])
async def list_sessions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Session).order_by(Session.start_time))
    return result.scalars().all()


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
