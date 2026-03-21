from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.telegram_user import TelegramUser


async def get_or_create_telegram_user(
    session: AsyncSession,
    telegram_id: int,
    username: str | None,
    first_name: str | None,
    last_name: str | None,
) -> TelegramUser:
    result = await session.execute(select(TelegramUser).where(TelegramUser.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if user:
        user.username = username
        user.first_name = first_name
        user.last_name = last_name
    else:
        user = TelegramUser(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
        )
        session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def get_by_telegram_id(session: AsyncSession, telegram_id: int) -> TelegramUser | None:
    result = await session.execute(select(TelegramUser).where(TelegramUser.telegram_id == telegram_id))
    return result.scalar_one_or_none()
