from datetime import datetime, timedelta, timezone
import re

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.user import purchase_tariff_keyboard, subscription_actions_keyboard, trial_confirm_keyboard
from bot.texts.messages import MARZBAN_TEMP_UNAVAILABLE, NO_ACCOUNT, TRIAL_ALREADY_USED, VPN_ACTIVATED
from config import Settings
from db.crud.profile import get_public_profiles
from db.crud.user import get_by_telegram_id
from db.crud.vpn_account import create_vpn_account, get_account_by_user_id, set_account_profiles
from db.models.telegram_user import TelegramUser
from services.marzban_client import MarzbanAPIError, MarzbanClient

router = Router(name="user_vpn")

CYR_TO_LAT = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e", "ж": "zh", "з": "z",
    "и": "i", "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o", "п": "p", "р": "r",
    "с": "s", "т": "t", "у": "u", "ф": "f", "х": "h", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sch",
    "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
}
USERNAME_ALLOWED = re.compile(r"[^a-z0-9_]+")

TARIFFS = {
    1: 200,
    2: 400,
    3: 600,
    4: 800,
    5: 500,
}


class TrialActivationState(StatesGroup):
    waiting_for_confirmation = State()
    waiting_for_username = State()


class PurchaseState(StatesGroup):
    waiting_for_tariff = State()


def devices_to_ip_limit(devices: int) -> int:
    if devices <= 0:
        return 2
    if devices == 1:
        return 2
    if devices == 2:
        return 3
    if devices == 3:
        return 4
    if devices == 4:
        return 5
    return devices + 2


def normalize_username(source: str) -> str:
    source = source.strip().lower()
    transliterated = "".join(CYR_TO_LAT.get(ch, ch) for ch in source)
    normalized = USERNAME_ALLOWED.sub("_", transliterated)
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    if not normalized:
        normalized = "user"
    return normalized[:32]


async def build_unique_username(base_username: str, marzban_client: MarzbanClient) -> str:
    candidate = base_username
    index = 1
    while True:
        try:
            await marzban_client.get_user(candidate)
            index += 1
            suffix = f"_{index}"
            candidate = f"{base_username[: 32 - len(suffix)]}{suffix}"
        except MarzbanAPIError:
            return candidate


@router.message(Command("profile"))
async def profile_command(message: Message, session: AsyncSession, state: FSMContext, marzban_client: MarzbanClient) -> None:
    await my_vpn(message, session, state, marzban_client)


@router.message(F.text.in_({"Мой VPN", "🛡️ Моя подписка", "🔐 Моя подписка"}))
async def my_vpn(message: Message, session: AsyncSession, state: FSMContext, marzban_client: MarzbanClient) -> None:
    user = await get_by_telegram_id(session, message.from_user.id)
    if not user:
        await message.answer(NO_ACCOUNT)
        return

    account = await get_account_by_user_id(session, user.id)
    if not account:
        await state.set_state(TrialActivationState.waiting_for_confirmation)
        await message.answer(
            "У вас нет активной подписки. Хотите получить пробный период?",
            reply_markup=trial_confirm_keyboard(),
        )
        return

    marzban_payload: dict | None = None
    try:
        marzban_payload = await marzban_client.get_user(account.marzban_username)
    except MarzbanAPIError:
        marzban_payload = None

    expire_at = account.expire_at
    if marzban_payload and marzban_payload.get("expire"):
        expire_at = datetime.fromtimestamp(marzban_payload["expire"], tz=timezone.utc)

    used_traffic = account.used_traffic_bytes
    up = marzban_payload.get("used_traffic", 0) if marzban_payload else 0
    down = marzban_payload.get("data_limit", 0) if marzban_payload else 0

    await message.answer(
        f"Статус: {'активен' if account.status == 'active' else 'не активен'}\n"
        f"Дата окончания: {expire_at.strftime('%d.%m.%Y') if expire_at else 'не задана'}\n"
        f"IP limit (устройства): {account.ip_limit}\n"
        f"Трафик входящий: {up / 1024**3:.2f} ГБ\n"
        f"Трафик исходящий: {down / 1024**3:.2f} ГБ\n"
        f"Трафик общий: {used_traffic / 1024**3:.2f} ГБ\n"
        f"Ключ:\n{account.subscription_url or 'пока не получен'}",
        reply_markup=subscription_actions_keyboard(),
    )


@router.message(TrialActivationState.waiting_for_confirmation, F.text.casefold() == "да")
async def trial_ask_username(message: Message, state: FSMContext, settings: Settings) -> None:
    if not settings.trial_enabled:
        await state.clear()
        await message.answer("Пробный период сейчас отключен.")
        return
    await state.set_state(TrialActivationState.waiting_for_username)
    await message.answer("Введите имя для создания VPN-пользователя.")


@router.message(TrialActivationState.waiting_for_confirmation, F.text.casefold() == "нет")
async def trial_decline(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Хорошо. Вы можете приобрести подписку в главном меню.")


@router.message(TrialActivationState.waiting_for_username)
async def trial_period_with_username(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    settings: Settings,
    marzban_client: MarzbanClient,
) -> None:
    requested_name = (message.text or "").strip()
    if not requested_name:
        await message.answer("Имя не может быть пустым. Введите имя заново.")
        return

    if not settings.trial_enabled:
        await state.clear()
        await message.answer("Пробный период сейчас отключен.")
        return

    user = await get_by_telegram_id(session, message.from_user.id)
    if not user:
        await state.clear()
        await message.answer("Нажмите /start для активации профиля в боте.")
        return

    profiles = await get_public_profiles(session)
    if not profiles:
        await state.clear()
        await message.answer("Нет доступных профилей. Обратитесь в поддержку.")
        return
    selected = profiles[0]

    lock_stmt = select(TelegramUser).where(TelegramUser.id == user.id).with_for_update()
    locked_user = (await session.execute(lock_stmt)).scalar_one()
    existing_account = await get_account_by_user_id(session, locked_user.id)
    if locked_user.trial_used or existing_account:
        await state.clear()
        await message.answer(TRIAL_ALREADY_USED)
        return

    normalized_name = normalize_username(requested_name)
    marzban_username = await build_unique_username(normalized_name, marzban_client)
    trial_days = settings.trial_days or 3
    ip_limit = devices_to_ip_limit(1)

    try:
        marzban_user = await marzban_client.create_user(
            username=marzban_username,
            expire_at=datetime.now(timezone.utc) + timedelta(days=trial_days),
            traffic_limit_gb=None,
            ip_limit=ip_limit,
            inbound_tags=selected.marzban_inbounds,
            note=f"tg_id={message.from_user.id}; requested={requested_name}",
        )
    except MarzbanAPIError:
        await message.answer(MARZBAN_TEMP_UNAVAILABLE)
        return

    account = await create_vpn_account(
        session,
        telegram_user_id=locked_user.id,
        marzban_username=marzban_username,
        subscription_url=marzban_user.get("subscription_url"),
        traffic_limit_gb=0,
        expire_days=trial_days,
        ip_limit=ip_limit,
    )
    await set_account_profiles(session, account.id, [selected.id], selected_profile_id=selected.id)
    locked_user.trial_used = True
    await session.commit()
    await state.clear()

    await message.answer(
        f"{VPN_ACTIVATED}\n"
        f"Логин: {marzban_username}\n"
        f"Пробный период: {trial_days} дн.\n"
        f"Трафик: без ограничений\n"
        f"IP limit: {ip_limit}"
    )


@router.message(F.text.in_({"Купить/Активировать доступ", "🔑 Приобрести подписку"}))
async def buy_or_activate(message: Message, state: FSMContext) -> None:
    await state.set_state(PurchaseState.waiting_for_tariff)
    await message.answer(
        "Выберите тариф:\n"
        "1 устройство = 200 руб\n"
        "2 устройства = 400 руб\n"
        "3 устройства = 600 руб\n"
        "4 устройства = 800 руб\n"
        "5 устройств = 500 руб",
        reply_markup=purchase_tariff_keyboard(),
    )


@router.message(PurchaseState.waiting_for_tariff)
async def process_tariff_choice(message: Message, state: FSMContext, settings: Settings) -> None:
    text = (message.text or "").strip()
    if text.lower() == "отмена":
        await state.clear()
        await message.answer("Операция отменена.")
        return

    match = re.match(r"^(\d+)\s+устрой", text)
    if not match:
        await message.answer("Выберите тариф кнопкой из списка.")
        return

    devices = int(match.group(1))
    price = TARIFFS.get(devices)
    if price is None:
        await message.answer("Этот тариф недоступен.")
        return

    ip_limit = devices_to_ip_limit(devices)
    await message.answer(f"Заявка принята: {devices} устройств, {price} ₽. Админ свяжется с вами.")

    if settings.admin_chat_id:
        await message.bot.send_message(
            settings.admin_chat_id,
            f"🧾 Новая заявка на подписку\n"
            f"Пользователь: @{message.from_user.username or '-'}\n"
            f"Telegram ID: {message.from_user.id}\n"
            f"Тариф: {devices} устройств / {price} ₽\n"
            f"Рекомендуемый ip_limit: {ip_limit}",
        )

    await state.clear()


@router.message(F.text == "QR-код")
async def get_qr_instruction(message: Message) -> None:
    await message.answer("Откройте приложение VPN и импортируйте подписку по ссылке — QR-код будет добавлен в следующем релизе.")


@router.message(F.text == "Скачать приложение")
async def download_app(message: Message) -> None:
    await message.answer("Рекомендуем Hiddify (Android) и Happ (iOS). Подробности в разделе «📖 Инструкция».")


@router.message(F.text == "Продлить")
async def renew_subscription(message: Message, settings: Settings) -> None:
    if settings.admin_chat_id:
        await message.bot.send_message(
            settings.admin_chat_id,
            f"🔁 Запрос на продление\nПользователь: @{message.from_user.username or '-'}\nTelegram ID: {message.from_user.id}",
        )
    await message.answer("Запрос на продление отправлен администратору.")
