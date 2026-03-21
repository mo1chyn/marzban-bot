from sqlalchemy import BigInteger, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base
from db.models.common import TimestampMixin


class TelegramUser(Base, TimestampMixin):
    __tablename__ = "telegram_users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    role: Mapped[str] = mapped_column(String(16), default="user", nullable=False)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    trial_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    vpn_accounts = relationship("VPNAccount", back_populates="telegram_user", lazy="selectin")
