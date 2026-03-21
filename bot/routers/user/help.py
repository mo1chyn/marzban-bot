from aiogram import F, Router
from aiogram.types import Message

from config import Settings

router = Router(name="user_help")

INSTRUCTION_TEXT = """
📱 Инструкции по подключению:

1) Android: установите Hiddify/Happ, добавьте ссылку подписки.
2) iPhone/iOS: установите Happ, вставьте ссылку и обновите подписку.
3) Как вставить ссылку: «Получить конфиг» → скопировать URL → вставить в приложение.
4) Как обновить подписку: откройте приложение и нажмите «Обновить».
5) Если оператор режет VPN: смените профиль через кнопку «Сменить профиль».
""".strip()


@router.message(F.text == "Инструкция")
async def instruction(message: Message) -> None:
    await message.answer(INSTRUCTION_TEXT)


@router.message(F.text == "Поддержка")
async def support(message: Message, settings: Settings) -> None:
    if settings.support_url:
        await message.answer(f"Поддержка: {settings.support_url}")
    else:
        await message.answer("Поддержка временно недоступна. Напишите администратору.")
