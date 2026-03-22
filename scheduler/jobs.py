from datetime import datetime, timedelta, timezone

from aiogram import Bot
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from config import Settings
from db.models.vpn_account import VPNAccount
from services.notification_service import NotificationService
from services.security_service import SecurityService


async def notify_expire_job(bot: Bot, session_factory: async_sessionmaker, settings: Settings) -> None:
    now = datetime.now(timezone.utc)
    async with session_factory() as session:
        for day in settings.notify_expire_days:
            target_start = now + timedelta(days=day)
            target_end = target_start + timedelta(hours=24)
            stmt = select(VPNAccount).where(VPNAccount.expire_at >= target_start, VPNAccount.expire_at < target_end)
            result = await session.execute(stmt)
            for account in result.scalars().all():
                await bot.send_message(
                    account.telegram_user.telegram_id,
                    f"Напоминание: ваш доступ истекает через {day} дн.",
                )


async def check_ip_sharing_job(bot: Bot, session_factory: async_sessionmaker, settings: Settings) -> None:
    notifier = NotificationService(bot=bot, admin_ids=settings.telegram_admin_ids)
    security_service = SecurityService(settings=settings, notifier=notifier)
    async with session_factory() as session:
        result = await session.execute(select(VPNAccount).where(VPNAccount.status == "active"))
        for account in result.scalars().all():
            await security_service.check_ip_sharing(session, account)
