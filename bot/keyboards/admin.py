from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def admin_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Создать пользователя"), KeyboardButton(text="Найти пользователя")],
            [KeyboardButton(text="Продлить доступ"), KeyboardButton(text="Сменить профиль")],
            [KeyboardButton(text="Сбросить трафик"), KeyboardButton(text="Отключить / включить")],
            [KeyboardButton(text="Удалить"), KeyboardButton(text="Посмотреть usage")],
            [KeyboardButton(text="Subscription URL"), KeyboardButton(text="Assigned profiles")],
            [KeyboardButton(text="История IP"), KeyboardButton(text="Подозрительный")],
            [KeyboardButton(text="Сообщение пользователю")],
        ],
        resize_keyboard=True,
    )
