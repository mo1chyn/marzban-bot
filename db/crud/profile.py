from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.profile import Profile


async def get_public_profiles(session: AsyncSession) -> list[Profile]:
    result = await session.execute(
        select(Profile)
        .where(Profile.enabled.is_(True), Profile.is_public.is_(True))
        .order_by(Profile.sort_order.asc(), Profile.id.asc())
    )
    return list(result.scalars().all())


async def get_default_profile(session: AsyncSession) -> Profile | None:
    result = await session.execute(select(Profile).where(Profile.enabled.is_(True), Profile.is_default.is_(True)))
    return result.scalar_one_or_none()


async def get_profile_by_code(session: AsyncSession, code: str) -> Profile | None:
    result = await session.execute(select(Profile).where(Profile.code == code, Profile.enabled.is_(True)))
    return result.scalar_one_or_none()
