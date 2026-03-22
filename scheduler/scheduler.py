from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import Settings
from db.session import SessionLocal
from scheduler.jobs import check_ip_sharing_job, notify_expire_job


def build_scheduler(bot, settings: Settings) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(notify_expire_job, "cron", hour=9, args=[bot, SessionLocal, settings])
    scheduler.add_job(check_ip_sharing_job, "interval", minutes=15, args=[bot, SessionLocal, settings])
    return scheduler
