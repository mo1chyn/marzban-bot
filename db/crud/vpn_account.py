from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.user_profile import UserProfile
from db.models.vpn_account import VPNAccount


async def get_account_by_user_id(session: AsyncSession, telegram_user_id: int) -> VPNAccount | None:
    result = await session.execute(select(VPNAccount).where(VPNAccount.telegram_user_id == telegram_user_id))
    return result.scalar_one_or_none()


async def create_vpn_account(
    session: AsyncSession,
    telegram_user_id: int,
    marzban_username: str,
    subscription_url: str | None,
    traffic_limit_gb: int,
    expire_days: int,
    ip_limit: int,
) -> VPNAccount:
    account = VPNAccount(
        telegram_user_id=telegram_user_id,
        marzban_username=marzban_username,
        subscription_url=subscription_url,
        traffic_limit_gb=traffic_limit_gb,
        expire_at=datetime.now(timezone.utc) + timedelta(days=expire_days),
        ip_limit=ip_limit,
    )
    session.add(account)
    await session.commit()
    await session.refresh(account)
    return account


async def set_account_profiles(
    session: AsyncSession,
    vpn_account_id: int,
    profile_ids: list[int],
    selected_profile_id: int | None = None,
) -> None:
    account = await session.get(VPNAccount, vpn_account_id)
    if account is None:
        return
    await session.execute(UserProfile.__table__.delete().where(UserProfile.vpn_account_id == vpn_account_id))
    for profile_id in profile_ids:
        session.add(
            UserProfile(
                vpn_account_id=vpn_account_id,
                profile_id=profile_id,
                is_selected=selected_profile_id == profile_id,
            )
        )
    await session.commit()
