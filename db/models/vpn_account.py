from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base
from db.models.common import TimestampMixin


class VPNAccount(Base, TimestampMixin):
    __tablename__ = "vpn_accounts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_user_id: Mapped[int] = mapped_column(ForeignKey("telegram_users.id", ondelete="CASCADE"), nullable=False)
    marzban_username: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    subscription_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="active", nullable=False)
    traffic_limit_gb: Mapped[int] = mapped_column(default=100, nullable=False)
    used_traffic_bytes: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    expire_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ip_limit: Mapped[int] = mapped_column(default=2, nullable=False)

    telegram_user = relationship("TelegramUser", back_populates="vpn_accounts", lazy="selectin")
    profiles = relationship("UserProfile", back_populates="vpn_account", lazy="selectin")
    ip_history = relationship("IPHistory", back_populates="vpn_account", lazy="selectin")
    suspicious_events = relationship("SuspiciousEvent", back_populates="vpn_account", lazy="selectin")
