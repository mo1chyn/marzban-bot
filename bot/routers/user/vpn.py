from datetime import datetime, timedelta, timezone
from uuid import uuid4

from aiogram import F, Router
from aiogram.types import Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.texts.messages import (
    MARZBAN_TEMP_UNAVAILABLE,
    NO_ACCOUNT,
    TRIAL_ALREADY_USED,
    VPN_ACTIVATED,
)
from config import Settings
from db.models.telegram_user import TelegramUser
from db.crud.profile import get_public_profiles
from db.crud.user import get_by_telegram_id
from db.crud.vpn_account import create_vpn_account, get_account_by_user_id, set_account_profiles
from services.marzban_client import MarzbanAPIError, MarzbanClient

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
    profiles = await get_public_profiles(session)
    if not profiles:
        await message.answer("Нет доступных профилей. Обратитесь в поддержку.")
        return
    selected = profiles[0]

    lock_stmt = select(TelegramUser).where(TelegramUser.id == user.id).with_for_update()
    locked_user = (await session.execute(lock_stmt)).scalar_one()
    existing_account = await get_account_by_user_id(session, locked_user.id)
    if locked_user.trial_used or existing_account:
        await message.answer(TRIAL_ALREADY_USED)
        return

    username = f"tg_{message.from_user.id}_{uuid4().hex[:8]}"
    try:
        marzban_user = await marzban_client.create_user(
            username=username,
            expire_at=datetime.now(timezone.utc) + timedelta(days=settings.trial_days),
            traffic_limit_gb=settings.trial_traffic_gb,
            ip_limit=settings.default_ip_limit,
            inbound_tags=selected.marzban_inbounds,
        )
    except MarzbanAPIError:
        await message.answer(MARZBAN_TEMP_UNAVAILABLE)
        return

    account = await create_vpn_account(
        session,
        telegram_user_id=locked_user.id,
        marzban_username=username,
        subscription_url=marzban_user.get("subscription_url"),
        traffic_limit_gb=settings.trial_traffic_gb,
        expire_days=settings.trial_days,
        ip_limit=settings.default_ip_limit,
    )
    await set_account_profiles(session, account.id, [selected.id], selected_profile_id=selected.id)
    locked_user.trial_used = True
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


@router.message(F.text == "Купить/Активировать доступ")
async def buy_or_activate(message: Message) -> None:
    await message.answer("Для активации доступа обратитесь в поддержку или к администратору.")


@router.message(F.text == "Мой трафик")
async def my_traffic(message: Message, session: AsyncSession) -> None:
    user = await get_by_telegram_id(session, message.from_user.id)
    if not user:
        await message.answer(NO_ACCOUNT)
        return
    account = await get_account_by_user_id(session, user.id)
    if not account:
        await message.answer(NO_ACCOUNT)
        return
    used_gb = account.used_traffic_bytes / 1024**3
    await message.answer(f"Использовано: {used_gb:.2f} ГБ из {account.traffic_limit_gb} ГБ.")


@router.message(F.text == "Мой срок")
async def my_expire(message: Message, session: AsyncSession) -> None:
    user = await get_by_telegram_id(session, message.from_user.id)
    if not user:
        await message.answer(NO_ACCOUNT)
        return
    account = await get_account_by_user_id(session, user.id)
    if not account:
        await message.answer(NO_ACCOUNT)
        return
    if not account.expire_at:
        await message.answer("Срок действия пока не задан.")
        return
    await message.answer(f"Доступ активен до {account.expire_at.strftime('%d.%m.%Y')}.")
