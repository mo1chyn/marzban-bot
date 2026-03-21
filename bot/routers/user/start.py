from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.user import main_user_keyboard
from bot.texts.messages import WELCOME
from db.crud.user import get_or_create_telegram_user

router = Router(name="user_start")


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession) -> None:
    await get_or_create_telegram_user(
        session=session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
    )
    await message.answer(WELCOME, reply_markup=main_user_keyboard())
