from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from db.crud.profile import get_profile_by_code, get_public_profiles
from db.crud.user import get_by_telegram_id
from db.crud.vpn_account import get_account_by_user_id, set_account_profiles
from services.marzban_client import MarzbanClient

router = Router(name="user_profile")


class SelectProfileState(StatesGroup):
    waiting_for_profile_code = State()


@router.message(F.text == "Сменить профиль")
async def start_profile_change(message: Message, state: FSMContext, session: AsyncSession) -> None:
    profiles = await get_public_profiles(session)
    if not profiles:
        await message.answer("Публичные профили недоступны.")
        return
    text = "Доступные профили:\n" + "\n".join([f"- {p.code}: {p.display_name}" for p in profiles])
    text += "\n\nОтправьте код профиля (например, RU_AUTO_YA)."
    await state.set_state(SelectProfileState.waiting_for_profile_code)
    await message.answer(text)


@router.message(SelectProfileState.waiting_for_profile_code)
async def apply_profile_change(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    marzban_client: MarzbanClient,
) -> None:
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

    await marzban_client.set_inbounds(account.marzban_username, profile.marzban_inbounds)
    await set_account_profiles(session, account.id, [profile.id], selected_profile_id=profile.id)

    await message.answer(f"Профиль подключен: {profile.display_name}")
    await state.clear()
