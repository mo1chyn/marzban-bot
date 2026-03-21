from aiogram import F, Router
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from config import Settings
from db.crud.admin import log_admin_action
from db.crud.user import get_by_telegram_id
from db.crud.vpn_account import get_account_by_user_id
from services.marzban_client import MarzbanClient

router = Router(name="admin_actions")


def is_admin(telegram_id: int, settings: Settings) -> bool:
    return telegram_id in settings.telegram_admin_ids


@router.message(F.text == "Найти пользователя")
async def find_user(message: Message, settings: Settings, session: AsyncSession) -> None:
    if not is_admin(message.from_user.id, settings):
        await message.answer("Недостаточно прав.")
        return
    await message.answer("Отправьте Telegram ID пользователя отдельным сообщением.")


@router.message(F.text.regexp(r"^\d{5,}$"))
async def find_user_by_telegram_id(message: Message, settings: Settings, session: AsyncSession) -> None:
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
    await marzban_client.reset_traffic(username)
    await log_admin_action(session, message.from_user.id, "reset_traffic", username)
    await message.answer(f"Трафик для {username} сброшен.")
