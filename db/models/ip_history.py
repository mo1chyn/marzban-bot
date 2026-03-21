from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base
from db.models.common import TimestampMixin


class IPHistory(Base, TimestampMixin):
    __tablename__ = "ip_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    vpn_account_id: Mapped[int] = mapped_column(ForeignKey("vpn_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    ip_address: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    country: Mapped[str | None] = mapped_column(String(64), nullable=True)

    vpn_account = relationship("VPNAccount", back_populates="ip_history", lazy="selectin")
