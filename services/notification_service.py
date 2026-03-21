from aiogram import Bot


class NotificationService:
    def __init__(self, bot: Bot, admin_ids: list[int]):
        self.bot = bot
        self.admin_ids = admin_ids

    async def notify_admins(self, text: str) -> None:
        for admin_id in self.admin_ids:
            await self.bot.send_message(admin_id, text)

    async def notify_user(self, telegram_id: int, text: str) -> None:
        await self.bot.send_message(telegram_id, text)
