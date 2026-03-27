from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from config import Settings

router = Router(name="user_help")


class SupportState(StatesGroup):
    waiting_for_message = State()


INSTRUCTION_TEXT = """
📱 Инструкции по подключению:

1) Android: установите Hiddify/Happ, добавьте ссылку подписки.
2) iPhone/iOS: установите Happ, вставьте ссылку и обновите подписку.
3) Как вставить ссылку: «Моя подписка» → скопировать URL → вставить в приложение.
4) Как обновить подписку: откройте приложение и нажмите «Обновить».
5) Если оператор режет VPN: смените профиль или напишите в поддержку.
""".strip()


@router.message(Command("support"))
async def support_command(message: Message, settings: Settings, state: FSMContext) -> None:
    await support(message, settings, state)


@router.message(Command("language"))
async def language_command(message: Message) -> None:
    await language(message)


@router.message(F.text.in_({"Инструкция", "📖 Инструкция"}))
async def instruction(message: Message) -> None:
    await message.answer(INSTRUCTION_TEXT)


@router.message(F.text.in_({"Поддержка", "💬 Поддержка", "Обратная связь", "💬 Обратная связь"}))
async def support(message: Message, settings: Settings, state: FSMContext) -> None:
    if settings.admin_chat_id:
        await state.set_state(SupportState.waiting_for_message)
        await message.answer("Напишите ваш вопрос одним сообщением — я передам его в поддержку.")
    else:
        await message.answer("Поддержка временно недоступна. Напишите администратору.")


@router.message(SupportState.waiting_for_message)
async def forward_support_message(message: Message, settings: Settings, state: FSMContext) -> None:
    if not settings.admin_chat_id:
        await state.clear()
        await message.answer("ADMIN_CHAT_ID не настроен. Сообщение не отправлено.")
        return

    user_name = message.from_user.username or "-"
    await message.bot.send_message(
        settings.admin_chat_id,
        "💬 Новое обращение в поддержку\n"
        f"username: @{user_name}\n"
        f"telegram_id: {message.from_user.id}\n"
        f"текст: {message.text or ''}",
    )
    await state.clear()
    await message.answer("Сообщение отправлено в поддержку. Ожидайте ответа.")


@router.message(F.text == "🤝 Пригласить друга")
async def invite_friend(message: Message) -> None:
    bot_user = await message.bot.get_me()
    await message.answer(
        "Отправьте другу ссылку на бота:\n"
        f"https://t.me/{bot_user.username}?start=ref_{message.from_user.id}"
    )


@router.message(F.text.in_({"📄 Правила сервиса", "📄 Правила"}))
async def service_rules(message: Message) -> None:
    await message.answer("Правила сервиса скоро появятся. Уточните детали у поддержки.")


@router.message(F.text.in_({"🌐 Language / Язык", "🌍 Язык"}))
async def language(message: Message) -> None:
    await message.answer("Смена языка скоро появится. Сейчас доступен русский язык.")
