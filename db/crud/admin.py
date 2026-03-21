from sqlalchemy.ext.asyncio import AsyncSession

from db.models.admin_action import AdminAction


async def log_admin_action(session: AsyncSession, admin_telegram_id: int, action: str, target: str, details: str = "") -> None:
    session.add(AdminAction(admin_telegram_id=admin_telegram_id, action=action, target=target, details=details))
    await session.commit()
