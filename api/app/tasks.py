import json
import logging
import uuid

from app.database import async_session
from app.services.inventory import release_expired_orders

logger = logging.getLogger(__name__)


def start_scheduler():
    from apscheduler.schedulers.asyncio import AsyncIOScheduler

    scheduler = AsyncIOScheduler()

    async def release_job():
        async with async_session() as db:
            count = await release_expired_orders(db)
            await db.commit()
            if count > 0:
                logger.info("Released %d expired orders", count)

    scheduler.add_job(release_job, "interval", minutes=1, id="release_expired")
    scheduler.start()
    return scheduler
