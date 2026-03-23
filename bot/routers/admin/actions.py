from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from bot.texts.messages import MARZBAN_TEMP_UNAVAILABLE
from config import Settings
from db.crud.admin import log_admin_action
from db.crud.user import get_by_telegram_id
from db.crud.vpn_account import get_account_by_user_id
from db.models.vpn_account import VPNAccount
from services.marzban_client import MarzbanAPIError, MarzbanClient

router = Router(name="admin_actions")


class AdminFindUserState(StatesGroup):
    waiting_for_telegram_id = State()


def is_admin(telegram_id: int, settings: Settings) -> bool:
    return telegram_id in settings.telegram_admin_ids


@router.message(F.text == "Найти пользователя")
async def find_user(message: Message, settings: Settings, state: FSMContext) -> None:
    if not is_admin(message.from_user.id, settings):
        await message.answer("Недостаточно прав.")
        return
    await state.set_state(AdminFindUserState.waiting_for_telegram_id)
    await message.answer("Отправьте Telegram ID пользователя отдельным сообщением.")


@router.message(AdminFindUserState.waiting_for_telegram_id, F.text.regexp(r"^\d{5,}$"))
async def find_user_by_telegram_id(
    message: Message, settings: Settings, session: AsyncSession, state: FSMContext
) -> None:
    if not is_admin(message.from_user.id, settings):
        return
    telegram_id = int(message.text)
    user = await get_by_telegram_id(session, telegram_id)
    if not user:
        await message.answer("Пользователь не найден в локальной БД.")
        return
    account = await get_account_by_user_id(session, user.id)
    if not account:
        await message.answer("Пользователь найден, но VPN-аккаунт отсутствует.")
        return
    await log_admin_action(session, message.from_user.id, "find_user", str(telegram_id))
    await message.answer(
        f"Пользователь найден:\nTelegram ID: {telegram_id}\nMarzban: {account.marzban_username}\nСтатус: {account.status}"
    )
    await state.clear()


@router.message(AdminFindUserState.waiting_for_telegram_id)
async def find_user_invalid_input(message: Message) -> None:
    await message.answer("Неверный формат. Введите Telegram ID (только цифры).")


@router.message(F.text == "Посмотреть usage")
async def get_usage_help(message: Message, settings: Settings) -> None:
    if not is_admin(message.from_user.id, settings):
        return
    await message.answer("Для MVP usage смотрите через поиск пользователя + Marzban API.")


@router.message(F.text == "Сбросить трафик")
async def reset_traffic_help(message: Message, settings: Settings, marzban_client: MarzbanClient) -> None:
    if not is_admin(message.from_user.id, settings):
        return
    await message.answer("Отправьте команду: /reset <marzban_username>")


@router.message(F.text.regexp(r"^/reset\s+\S+"))
async def reset_traffic(message: Message, settings: Settings, session: AsyncSession, marzban_client: MarzbanClient) -> None:
    if not is_admin(message.from_user.id, settings):
        return
    username = message.text.split(maxsplit=1)[1].strip()
    try:
        await marzban_client.reset_traffic(username)
    except MarzbanAPIError:
        await message.answer(MARZBAN_TEMP_UNAVAILABLE)
        return
    await log_admin_action(session, message.from_user.id, "reset_traffic", username)
    await message.answer(f"Трафик для {username} сброшен.")


@router.message(F.text.regexp(r"^/setiplimit\s+\S+\s+\d+$"))
async def set_ip_limit(
    message: Message,
    settings: Settings,
    session: AsyncSession,
    marzban_client: MarzbanClient,
) -> None:
    if not is_admin(message.from_user.id, settings):
        return

    _, username, ip_limit_raw = message.text.split(maxsplit=2)
    ip_limit = int(ip_limit_raw)
    if ip_limit < 1 or ip_limit > 16:
        await message.answer("IP-лимит должен быть в диапазоне 1..16.")
        return

    stmt = select(VPNAccount).where(VPNAccount.marzban_username == username)
    account = (await session.execute(stmt)).scalar_one_or_none()
    if not account:
        await message.answer("Аккаунт не найден в локальной БД.")
        return

    try:
        await marzban_client.update_user(username, {"ip_limit": ip_limit})
    except MarzbanAPIError:
        await message.answer(MARZBAN_TEMP_UNAVAILABLE)
        return

    account.ip_limit = ip_limit
    await session.commit()
    await log_admin_action(session, message.from_user.id, "set_ip_limit", f"{username}:{ip_limit}")
    await message.answer(f"IP-лимит для {username} обновлён: {ip_limit}")
