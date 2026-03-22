from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from config import Settings
from db.crud.security import add_suspicious_event
from db.models.ip_history import IPHistory
from db.models.vpn_account import VPNAccount
from services.notification_service import NotificationService


class SecurityService:
    def __init__(self, settings: Settings, notifier: NotificationService):
        self.settings = settings
        self.notifier = notifier

    async def check_ip_sharing(self, session: AsyncSession, account: VPNAccount) -> bool:
        window_start = datetime.now(timezone.utc) - timedelta(hours=24)
        stmt = (
            select(func.count(func.distinct(IPHistory.ip_address)))
            .where(IPHistory.vpn_account_id == account.id)
            .where(IPHistory.created_at >= window_start)
        )
        result = await session.execute(stmt)
        unique_ip_count = result.scalar_one() or 0

        if unique_ip_count <= account.ip_limit:
            return False

        message = f"У пользователя {account.marzban_username} превышен IP-лимит: {unique_ip_count}/{account.ip_limit}"
        auto_blocked = self.settings.auto_block_on_sharing and not self.settings.sharing_notify_only

        await add_suspicious_event(session, account.id, "ip_sharing", message, auto_blocked=auto_blocked)
        await self.notifier.notify_admins(f"⚠️ Suspicious event: {message}")

        if auto_blocked:
            account.status = "disabled"
            await session.commit()
        return True
