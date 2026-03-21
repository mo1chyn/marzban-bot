from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base
from db.models.common import TimestampMixin


class SuspiciousEvent(Base, TimestampMixin):
    __tablename__ = "suspicious_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    vpn_account_id: Mapped[int] = mapped_column(ForeignKey("vpn_accounts.id", ondelete="CASCADE"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    auto_blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    vpn_account = relationship("VPNAccount", back_populates="suspicious_events", lazy="selectin")
