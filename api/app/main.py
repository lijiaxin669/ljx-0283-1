from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, Base
from app.routers import sessions, orders, payments, admin
from app.tasks import start_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    scheduler = start_scheduler()
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(
    title="少年宫亲子游泳班报名系统",
    description="场次库存行级锁 · 下单15分钟未支付自动释放 · 支付回调幂等键payment_id",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sessions.router, prefix="/api/sessions", tags=["场次"])
app.include_router(orders.router, prefix="/api/orders", tags=["订单"])
app.include_router(payments.router, prefix="/api/payments", tags=["支付"])
app.include_router(admin.router, prefix="/api/admin", tags=["管理"])
