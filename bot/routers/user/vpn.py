from datetime import datetime, timedelta, timezone

from aiogram import F, Router
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.texts.messages import NO_ACCOUNT, TRIAL_ALREADY_USED, VPN_ACTIVATED
from config import Settings
from db.crud.profile import get_public_profiles
from db.crud.user import get_by_telegram_id
from db.crud.vpn_account import create_vpn_account, get_account_by_user_id, set_account_profiles
from services.marzban_client import MarzbanClient

router = Router(name="user_vpn")


@router.message(F.text == "Мой VPN")
async def my_vpn(message: Message, session: AsyncSession) -> None:
    user = await get_by_telegram_id(session, message.from_user.id)
    if not user:
        await message.answer(NO_ACCOUNT)
        return
    account = await get_account_by_user_id(session, user.id)
    if not account:
        await message.answer(NO_ACCOUNT)
        return
    expire_text = account.expire_at.strftime("%d.%m.%Y") if account.expire_at else "не задан"
    await message.answer(
        f"Статус: {account.status}\n"
        f"Логин: {account.marzban_username}\n"
        f"Срок до: {expire_text}\n"
        f"Ссылка подписки:\n{account.subscription_url or 'еще не получена'}"
    )


@router.message(F.text == "Пробный период")
async def trial_period(
    message: Message,
    session: AsyncSession,
    settings: Settings,
    marzban_client: MarzbanClient,
) -> None:
    if not settings.trial_enabled:
        await message.answer("Пробный период сейчас отключен.")
        return
    user = await get_by_telegram_id(session, message.from_user.id)
    if not user:
        await message.answer("Нажмите /start для активации профиля в боте.")
        return
    if user.trial_used:
        await message.answer(TRIAL_ALREADY_USED)
        return

    username = f"tg_{message.from_user.id}"
    profiles = await get_public_profiles(session)
    if not profiles:
        await message.answer("Нет доступных профилей. Обратитесь в поддержку.")
        return
    selected = profiles[0]

    marzban_user = await marzban_client.create_user(
        username=username,
        expire_at=datetime.now(timezone.utc) + timedelta(days=settings.trial_days),
        traffic_limit_gb=settings.trial_traffic_gb,
        ip_limit=settings.default_ip_limit,
        inbound_tags=selected.marzban_inbounds,
    )

    account = await create_vpn_account(
        session,
        telegram_user_id=user.id,
        marzban_username=username,
        subscription_url=marzban_user.get("subscription_url"),
        traffic_limit_gb=settings.trial_traffic_gb,
        expire_days=settings.trial_days,
        ip_limit=settings.default_ip_limit,
    )
    await set_account_profiles(session, account.id, [selected.id], selected_profile_id=selected.id)
    user.trial_used = True
    await session.commit()

    await message.answer(f"{VPN_ACTIVATED}\nПробный период: {settings.trial_days} дн.\nТрафик: {settings.trial_traffic_gb} ГБ")


@router.message(F.text == "Получить конфиг")
async def get_config(message: Message, session: AsyncSession) -> None:
    user = await get_by_telegram_id(session, message.from_user.id)
    if not user:
        await message.answer(NO_ACCOUNT)
        return
    account = await get_account_by_user_id(session, user.id)
    if not account or not account.subscription_url:
        await message.answer("Конфиг пока недоступен.")
        return
    await message.answer(f"Ваша ссылка подписки:\n{account.subscription_url}")
