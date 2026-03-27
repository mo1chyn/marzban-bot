from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def main_user_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔐 Моя подписка")],
            [KeyboardButton(text="🔑 Приобрести подписку")],
            [KeyboardButton(text="📖 Инструкция"), KeyboardButton(text="💬 Поддержка")],
            [KeyboardButton(text="🤝 Пригласить друга")],
            [KeyboardButton(text="📄 Правила")],
            [KeyboardButton(text="🌍 Язык")],
        ],
        resize_keyboard=True,
    )


def trial_confirm_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Да"), KeyboardButton(text="Нет")]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def purchase_tariff_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="1 устройство — 200 ₽")],
            [KeyboardButton(text="2 устройства — 400 ₽")],
            [KeyboardButton(text="3 устройства — 600 ₽")],
            [KeyboardButton(text="4 устройства — 800 ₽")],
            [KeyboardButton(text="5 устройств — 500 ₽")],
            [KeyboardButton(text="Отмена")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def subscription_actions_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="QR-код"), KeyboardButton(text="Скачать приложение")],
            [KeyboardButton(text="Продлить"), KeyboardButton(text="💬 Поддержка")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
