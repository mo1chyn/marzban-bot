from sqlalchemy.ext.asyncio import AsyncSession

from db.models.ip_history import IPHistory
from db.models.suspicious_event import SuspiciousEvent


async def add_ip_history(session: AsyncSession, vpn_account_id: int, ip_address: str, country: str | None = None) -> None:
    session.add(IPHistory(vpn_account_id=vpn_account_id, ip_address=ip_address, country=country))
    await session.commit()


async def add_suspicious_event(
    session: AsyncSession,
    vpn_account_id: int,
    event_type: str,
    message: str,
    auto_blocked: bool,
) -> SuspiciousEvent:
    event = SuspiciousEvent(
        vpn_account_id=vpn_account_id,
        event_type=event_type,
        message=message,
        auto_blocked=auto_blocked,
    )
    session.add(event)
    await session.commit()
    await session.refresh(event)
    return event
