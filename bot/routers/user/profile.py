from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.texts.messages import MARZBAN_TEMP_UNAVAILABLE
from db.crud.profile import get_profile_by_code, get_public_profiles
from db.crud.user import get_by_telegram_id
from db.crud.vpn_account import get_account_by_user_id, set_account_profiles
from services.marzban_client import MarzbanAPIError, MarzbanClient

router = Router(name="user_profile")


class SelectProfileState(StatesGroup):
    waiting_for_profile_code = State()


@router.message(F.text == "Сменить профиль")
async def start_profile_change(message: Message, state: FSMContext, session: AsyncSession) -> None:
    profiles = await get_public_profiles(session)
    if not profiles:
        await message.answer("Публичные профили недоступны.")
        return
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=profile.display_name, callback_data=f"profile:{profile.code}")]
            for profile in profiles
        ]
    )
    await state.set_state(SelectProfileState.waiting_for_profile_code)
    await message.answer("Выберите профиль кнопкой ниже.", reply_markup=keyboard)


@router.message(SelectProfileState.waiting_for_profile_code)
async def apply_profile_change(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    marzban_client: MarzbanClient,
) -> None:
    if not message.text:
        return
    profile = await get_profile_by_code(session, message.text.strip())
    if not profile or not profile.is_public:
        await message.answer("Профиль не найден или недоступен. Попробуйте снова.")
        return

    user = await get_by_telegram_id(session, message.from_user.id)
    if not user:
        await message.answer("Сначала отправьте /start")
        await state.clear()
        return

    account = await get_account_by_user_id(session, user.id)
    if not account:
        await message.answer("Аккаунт не найден.")
        await state.clear()
        return

    try:
        await marzban_client.set_inbounds(account.marzban_username, profile.marzban_inbounds)
    except MarzbanAPIError:
        await message.answer(MARZBAN_TEMP_UNAVAILABLE)
        return
    await set_account_profiles(session, account.id, [profile.id], selected_profile_id=profile.id)

    await message.answer(f"Профиль подключен: {profile.display_name}")
    await state.clear()


@router.callback_query(StateFilter(SelectProfileState.waiting_for_profile_code), F.data.startswith("profile:"))
async def apply_profile_change_by_button(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    marzban_client: MarzbanClient,
) -> None:
    profile_code = callback.data.split(":", maxsplit=1)[1]
    profile = await get_profile_by_code(session, profile_code)
    if not profile or not profile.is_public:
        await callback.message.answer("Профиль не найден или недоступен.")
        await callback.answer()
        return

    user = await get_by_telegram_id(session, callback.from_user.id)
    if not user:
        await callback.message.answer("Сначала отправьте /start")
        await state.clear()
        await callback.answer()
        return

    account = await get_account_by_user_id(session, user.id)
    if not account:
        await callback.message.answer("Аккаунт не найден.")
        await state.clear()
        await callback.answer()
        return

    try:
        await marzban_client.set_inbounds(account.marzban_username, profile.marzban_inbounds)
    except MarzbanAPIError:
        await callback.message.answer(MARZBAN_TEMP_UNAVAILABLE)
        await callback.answer()
        return

    await set_account_profiles(session, account.id, [profile.id], selected_profile_id=profile.id)
    await callback.message.answer(f"Профиль подключен: {profile.display_name}")
    await state.clear()
    await callback.answer()
