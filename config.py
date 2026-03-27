from functools import lru_cache
from typing import Annotated, List

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    telegram_bot_token: str = Field(alias="TELEGRAM_BOT_TOKEN")
    telegram_admin_ids: Annotated[List[int], NoDecode] = Field(
        default_factory=list,
        validation_alias=AliasChoices("TELEGRAM_ADMIN_IDS", "ADMIN_IDS"),
    )
    telegram_support_ids: Annotated[List[int], NoDecode] = Field(default_factory=list, alias="TELEGRAM_SUPPORT_IDS")
    admin_chat_id: int = Field(default=0, validation_alias=AliasChoices("ADMIN_CHAT_ID", "TELEGRAM_ADMIN_CHAT_ID"))

    marzban_base_url: str = Field(validation_alias=AliasChoices("MARZBAN_BASE_URL", "MARZBAN_URL"))
    marzban_username: str = Field(alias="MARZBAN_USERNAME")
    marzban_password: str = Field(alias="MARZBAN_PASSWORD")
    marzban_token: str = Field(default="", validation_alias=AliasChoices("MARZBAN_TOKEN"))
    marzban_timeout_seconds: int = Field(default=15, alias="MARZBAN_TIMEOUT_SECONDS")
    marzban_retry_count: int = Field(default=3, alias="MARZBAN_RETRY_COUNT")

    marzban_endpoint_token: str = Field(default="/api/admin/token", alias="MARZBAN_ENDPOINT_TOKEN")
    marzban_endpoint_users: str = Field(default="/api/user", alias="MARZBAN_ENDPOINT_USERS")
    marzban_endpoint_user_by_name: str = Field(default="/api/user/{username}", alias="MARZBAN_ENDPOINT_USER_BY_NAME")
    marzban_endpoint_reset_traffic: str = Field(default="/api/user/{username}/reset", alias="MARZBAN_ENDPOINT_RESET_TRAFFIC")
    marzban_endpoint_usage: str = Field(default="/api/user/{username}/usage", alias="MARZBAN_ENDPOINT_USAGE")
    marzban_endpoint_online_users: str = Field(default="/api/users/online", alias="MARZBAN_ENDPOINT_ONLINE_USERS")
    marzban_protocol: str = Field(default="vless", alias="MARZBAN_PROTOCOL")

    database_url: str = Field(default="sqlite+aiosqlite:///./app.db", alias="DATABASE_URL")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    default_ip_limit: int = Field(default=2, alias="DEFAULT_IP_LIMIT")
    default_traffic_limit_gb: int = Field(default=100, alias="DEFAULT_TRAFFIC_LIMIT_GB")
    default_expire_days: int = Field(default=30, alias="DEFAULT_EXPIRE_DAYS")

    trial_enabled: bool = Field(default=True, alias="TRIAL_ENABLED")
    trial_days: int = Field(default=3, alias="TRIAL_DAYS")
    trial_traffic_gb: int = Field(default=5, alias="TRIAL_TRAFFIC_GB")

    sharing_notify_only: bool = Field(default=True, alias="SHARING_NOTIFY_ONLY")
    auto_block_on_sharing: bool = Field(default=False, alias="AUTO_BLOCK_ON_SHARING")

    default_profile_code: str = Field(default="", alias="DEFAULT_PROFILE_CODE")
    support_url: str = Field(default="", alias="SUPPORT_URL")
    notify_expire_days: Annotated[List[int], NoDecode] = Field(default_factory=lambda: [3, 1], alias="NOTIFY_EXPIRE_DAYS")

    @field_validator("telegram_admin_ids", "telegram_support_ids", mode="before")
    @classmethod
    def parse_int_list(cls, value: str | list[int]) -> list[int]:
        if isinstance(value, list):
            return value
        if not value:
            return []
        return [int(v.strip()) for v in value.split(",") if v.strip()]

    @field_validator("notify_expire_days", mode="before")
    @classmethod
    def parse_days_list(cls, value: str | list[int]) -> list[int]:
        if isinstance(value, list):
            return value
        if not value:
            return [3, 1]
        return [int(v.strip()) for v in value.split(",") if v.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
