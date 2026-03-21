from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def main_user_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Купить/Активировать доступ"), KeyboardButton(text="Пробный период")],
            [KeyboardButton(text="Мой VPN"), KeyboardButton(text="Мой трафик"), KeyboardButton(text="Мой срок")],
            [KeyboardButton(text="Получить конфиг"), KeyboardButton(text="Сменить профиль")],
            [KeyboardButton(text="Инструкция"), KeyboardButton(text="Поддержка")],
        ],
        resize_keyboard=True,
    )
