from aiogram import F, Router
from aiogram.types import Message

from bot.keyboards.admin import admin_keyboard
from config import Settings

router = Router(name="admin_panel")


@router.message(F.text == "/admin")
async def admin_panel(message: Message, settings: Settings) -> None:
    if message.from_user.id not in settings.telegram_admin_ids:
        await message.answer("Недостаточно прав.")
        return
    await message.answer("Админ-панель", reply_markup=admin_keyboard())
