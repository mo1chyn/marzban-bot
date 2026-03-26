from aiogram import F, Router
from aiogram.filters import Command
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


@router.message(Command("support"))
async def support_command(message: Message, settings: Settings) -> None:
    await support(message, settings)


@router.message(Command("language"))
async def language_command(message: Message) -> None:
    await language(message)


@router.message(F.text.in_({"Инструкция", "📖 Инструкция"}))
async def instruction(message: Message) -> None:
    await message.answer(INSTRUCTION_TEXT)


@router.message(F.text.in_({"Поддержка", "💬 Поддержка"}))
async def support(message: Message, settings: Settings) -> None:
    if settings.support_url:
        await message.answer(f"Поддержка: {settings.support_url}")
    else:
        await message.answer("Поддержка временно недоступна. Напишите администратору.")


@router.message(F.text == "🤝 Пригласить друга")
async def invite_friend(message: Message) -> None:
    bot_user = await message.bot.get_me()
    await message.answer(
        "Отправьте другу ссылку на бота:\n"
        f"https://t.me/{bot_user.username}?start=ref_{message.from_user.id}"
    )


@router.message(F.text == "📄 Правила сервиса")
async def service_rules(message: Message) -> None:
    await message.answer("Правила сервиса скоро появятся. Уточните детали у поддержки.")


@router.message(F.text == "🌐 Language / Язык")
async def language(message: Message) -> None:
    await message.answer("Смена языка скоро появится. Сейчас доступен русский язык.")
