import logging
from datetime import datetime, timedelta, timezone

from aiogram import Bot
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from config import Settings
from db.crud.security import add_ip_history
from db.models.vpn_account import VPNAccount
from services.marzban_client import MarzbanClient
from services.notification_service import NotificationService
from services.security_service import SecurityService

logger = logging.getLogger(__name__)


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


async def check_ip_sharing_job(
    bot: Bot,
    session_factory: async_sessionmaker,
    settings: Settings,
    marzban_client: MarzbanClient,
) -> None:
    notifier = NotificationService(bot=bot, admin_ids=settings.telegram_admin_ids)
    security_service = SecurityService(settings=settings, notifier=notifier)

    username_to_ips: dict[str, set[str]] = {}
    try:
        online_users = await marzban_client.get_online_users()
        for user in online_users:
            username = user.get("username")
            if not username:
                continue

            raw_ip = user.get("ip") or user.get("ip_address")
            if isinstance(raw_ip, str) and raw_ip:
                username_to_ips.setdefault(username, set()).add(raw_ip)

            raw_ips = user.get("ips")
            if isinstance(raw_ips, list):
                for ip in raw_ips:
                    if isinstance(ip, str) and ip:
                        username_to_ips.setdefault(username, set()).add(ip)
    except Exception as exc:
        logger.error("Не удалось получить онлайн-пользователей Marzban: %s", exc)

    async with session_factory() as session:
        result = await session.execute(select(VPNAccount).where(VPNAccount.status == "active"))
        for account in result.scalars().all():
            for ip in username_to_ips.get(account.marzban_username, set()):
                await add_ip_history(session, account.id, ip)

            try:
                used_traffic_bytes = await marzban_client.get_user_used_traffic_bytes(account.marzban_username)
                if used_traffic_bytes is not None:
                    account.used_traffic_bytes = used_traffic_bytes
            except Exception as exc:
                logger.error("Не удалось синхронизировать трафик для %s: %s", account.marzban_username, exc)

            await security_service.check_ip_sharing(session, account)
        await session.commit()
