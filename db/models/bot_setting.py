from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base
from db.models.common import TimestampMixin


class BotSetting(Base, TimestampMixin):
    __tablename__ = "bot_settings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
