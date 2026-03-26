from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def main_user_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛡️ Моя подписка")],
            [KeyboardButton(text="🔑 Приобрести подписку")],
            [KeyboardButton(text="📖 Инструкция"), KeyboardButton(text="💬 Поддержка")],
            [KeyboardButton(text="🤝 Пригласить друга")],
            [KeyboardButton(text="📄 Правила сервиса")],
            [KeyboardButton(text="🌐 Language / Язык")],
        ],
        resize_keyboard=True,
    )
