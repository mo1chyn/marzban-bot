from sqlalchemy.ext.asyncio import AsyncSession

from config import Settings
from db.crud.profile import get_default_profile, get_profile_by_code, get_public_profiles
from db.models.profile import Profile


class ProfileService:
    def __init__(self, settings: Settings):
        self._settings = settings

    async def get_public_profiles(self, session: AsyncSession) -> list[Profile]:
        return await get_public_profiles(session)

    async def choose_default_profile(self, session: AsyncSession) -> Profile | None:
        if self._settings.default_profile_code:
            profile = await get_profile_by_code(session, self._settings.default_profile_code)
            if profile and profile.is_public:
                return profile
        return await get_default_profile(session)
