import asyncio
import logging
from datetime import datetime
from typing import Any

import httpx

from config import Settings

logger = logging.getLogger(__name__)


class MarzbanAPIError(Exception):
    pass


class MarzbanAuthError(MarzbanAPIError):
    pass


class MarzbanClient:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._token: str | None = None
        self._client = httpx.AsyncClient(
            base_url=self._settings.marzban_base_url,
            timeout=self._settings.marzban_timeout_seconds,
        )

    async def close(self) -> None:
        await self._client.aclose()

    def _endpoint(self, template: str, **kwargs: Any) -> str:
        return template.format(**kwargs)

    async def _authenticate(self) -> None:
        if self._settings.marzban_token:
            self._token = self._settings.marzban_token
            return

        response = await self._client.post(
            self._settings.marzban_endpoint_token,
            data={"username": self._settings.marzban_username, "password": self._settings.marzban_password},
        )
        if response.status_code >= 400:
            raise MarzbanAuthError(f"Ошибка авторизации Marzban: {response.status_code}")
        payload = response.json()
        self._token = payload.get("access_token")
        if not self._token:
            raise MarzbanAuthError("Marzban не вернул access_token")

    async def _request(self, method: str, endpoint: str, json: dict[str, Any] | None = None) -> dict[str, Any]:
        if not self._token:
            await self._authenticate()

        last_exception: Exception | None = None
        for attempt in range(self._settings.marzban_retry_count):
            try:
                response = await self._client.request(
                    method,
                    endpoint,
                    json=json,
                    headers={"Authorization": f"Bearer {self._token}"},
                )
                if response.status_code == 401:
                    await self._authenticate()
                    continue
                if response.status_code >= 400:
                    raise MarzbanAPIError(f"Marzban error {response.status_code}: {response.text}")
                if response.content:
                    return response.json()
                return {}
            except (httpx.HTTPError, MarzbanAPIError) as exc:
                logger.error("Ошибка запроса к Marzban: %s", exc)
                last_exception = exc
                await asyncio.sleep(0.5 * (attempt + 1))
        raise MarzbanAPIError(f"Не удалось выполнить запрос к Marzban: {last_exception}")

    async def create_user(
        self,
        username: str,
        expire_at: datetime,
        traffic_limit_gb: int | None,
        ip_limit: int,
        inbound_tags: list[str],
        protocol: str | None = None,
        note: str = "created by telegram bot",
    ) -> dict[str, Any]:
        selected_protocol = protocol or self._settings.marzban_protocol
        data_limit = 0 if traffic_limit_gb is None else traffic_limit_gb * 1024**3
        payload = {
            "username": username,
            "status": "active",
            "expire": int(expire_at.timestamp()),
            "data_limit": data_limit,
            "proxies": {},
            "inbounds": {selected_protocol: inbound_tags},
            "on_hold_timeout": 0,
            "note": note,
            "ip_limit": ip_limit,
        }
        return await self._request("POST", self._settings.marzban_endpoint_users, json=payload)

    async def get_user(self, username: str) -> dict[str, Any]:
        return await self._request("GET", self._endpoint(self._settings.marzban_endpoint_user_by_name, username=username))

    async def update_user(self, username: str, payload: dict[str, Any]) -> dict[str, Any]:
        return await self._request(
            "PUT",
            self._endpoint(self._settings.marzban_endpoint_user_by_name, username=username),
            json=payload,
        )

    async def delete_user(self, username: str) -> dict[str, Any]:
        return await self._request("DELETE", self._endpoint(self._settings.marzban_endpoint_user_by_name, username=username))

    async def reset_traffic(self, username: str) -> dict[str, Any]:
        return await self._request(
            "POST", self._endpoint(self._settings.marzban_endpoint_reset_traffic, username=username)
        )

    async def enable_disable_user(self, username: str, enabled: bool) -> dict[str, Any]:
        return await self.update_user(username, {"status": "active" if enabled else "disabled"})

    async def get_usage(self, username: str) -> dict[str, Any]:
        return await self._request("GET", self._endpoint(self._settings.marzban_endpoint_usage, username=username))

    async def get_user_used_traffic_bytes(self, username: str) -> int | None:
        """Возвращает использованный трафик пользователя в байтах, если поле найдено в API."""
        user_payload = await self.get_user(username)
        used = self._extract_used_traffic_bytes(user_payload)
        if used is not None:
            return used

        usage_payload = await self.get_usage(username)
        return self._extract_used_traffic_bytes(usage_payload)

    @staticmethod
    def _extract_used_traffic_bytes(payload: dict[str, Any]) -> int | None:
        candidates = (
            "used_traffic",
            "used_traffic_bytes",
            "data_limit_used",
            "traffic_used",
            "up",
            "download",
        )
        for field in candidates:
            value = payload.get(field)
            if isinstance(value, (int, float)) and value >= 0:
                return int(value)

        usages = payload.get("usages")
        if isinstance(usages, dict):
            total = usages.get("total")
            if isinstance(total, (int, float)) and total >= 0:
                return int(total)
        return None

    async def get_online_users(self) -> list[dict[str, Any]]:
        """
        Возвращает онлайн-пользователей из Marzban.

        В зависимости от версии API ответ может быть:
        - {"users": [{...}, ...]}
        - [{...}, ...]
        """
        result = await self._request("GET", self._settings.marzban_endpoint_online_users)
        if isinstance(result, list):
            return [entry for entry in result if isinstance(entry, dict)]

        users = result.get("users", [])
        if isinstance(users, list):
            return [entry for entry in users if isinstance(entry, dict)]
        return []

    async def set_inbounds(
        self,
        username: str,
        inbound_tags: list[str],
        protocol: str | None = None,
    ) -> dict[str, Any]:
        user = await self.get_user(username)
        selected_protocol = protocol or self._settings.marzban_protocol
        current_inbounds = user.get("inbounds") or {}
        if not isinstance(current_inbounds, dict):
            current_inbounds = {}
        current_inbounds[selected_protocol] = inbound_tags
        user["inbounds"] = current_inbounds
        return await self.update_user(username, user)
