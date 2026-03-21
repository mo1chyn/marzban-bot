from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base
from db.models.common import TimestampMixin


class UserProfile(Base, TimestampMixin):
    __tablename__ = "user_profiles"
    __table_args__ = (UniqueConstraint("vpn_account_id", "profile_id", name="uq_user_profile_link"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    vpn_account_id: Mapped[int] = mapped_column(ForeignKey("vpn_accounts.id", ondelete="CASCADE"), nullable=False)
    profile_id: Mapped[int] = mapped_column(ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    is_selected: Mapped[bool] = mapped_column(default=False, nullable=False)

    vpn_account = relationship("VPNAccount", back_populates="profiles", lazy="selectin")
    profile = relationship("Profile", back_populates="user_links", lazy="selectin")
