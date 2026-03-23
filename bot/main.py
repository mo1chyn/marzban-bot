import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.types import TelegramObject
from aiogram.dispatcher.middlewares.base import BaseMiddleware

from bot.routers.admin.actions import router as admin_actions_router
from bot.routers.admin.panel import router as admin_panel_router
from bot.routers.user.help import router as user_help_router
from bot.routers.user.profile import router as user_profile_router
from bot.routers.user.start import router as user_start_router
from bot.routers.user.vpn import router as user_vpn_router
from config import Settings, get_settings
from db.session import SessionLocal
from logging_config import setup_logging
from scheduler.scheduler import build_scheduler
from services.marzban_client import MarzbanClient


class DbSessionMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: TelegramObject, data: dict):
        async with SessionLocal() as session:
            data["session"] = session
            return await handler(event, data)


class SettingsMiddleware(BaseMiddleware):
    def __init__(self, settings: Settings):
        self.settings = settings

    async def __call__(self, handler, event: TelegramObject, data: dict):
        data["settings"] = self.settings
        return await handler(event, data)


class MarzbanMiddleware(BaseMiddleware):
    def __init__(self, marzban_client: MarzbanClient):
        self.marzban_client = marzban_client

    async def __call__(self, handler, event: TelegramObject, data: dict):
        data["marzban_client"] = self.marzban_client
        return await handler(event, data)


async def main() -> None:
    settings = get_settings()
    setup_logging(settings.log_level)

    bot = Bot(token=settings.telegram_bot_token)
    dp = Dispatcher()

    marzban_client = MarzbanClient(settings)

    dp.update.middleware(SettingsMiddleware(settings))
    dp.update.middleware(DbSessionMiddleware())
    dp.update.middleware(MarzbanMiddleware(marzban_client))

    dp.include_router(user_start_router)
    dp.include_router(user_vpn_router)
    dp.include_router(user_profile_router)
    dp.include_router(user_help_router)
    dp.include_router(admin_panel_router)
    dp.include_router(admin_actions_router)

    scheduler = build_scheduler(bot, settings, marzban_client)
    scheduler.start()

    try:
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown(wait=False)
        await marzban_client.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
