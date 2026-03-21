# Marzban Telegram Bot (MVP)

Русскоязычный MVP Telegram-бот для управления VPN-доступом через Marzban API.

## Возможности MVP
- Русский UI для клиента и админа
- Интеграция с Marzban API (auth, create/get/update/delete user, reset traffic, usage, inbounds)
- Профили подключения (универсальная модель без хардкода под конкретное число серверов)
- Выдача пробного периода (1 раз на Telegram ID)
- Базовый антишаринг: лимит IP, suspicious events, авто/ручная реакция
- Планировщик уведомлений (APScheduler)
- Async-архитектура: aiogram 3 + SQLAlchemy async + httpx async
- Alembic миграции

## Структура
- `bot/` — Telegram обработчики, тексты и клавиатуры
- `db/` — модели, сессии и CRUD
- `services/` — Marzban client, безопасность, профили, уведомления
- `scheduler/` — фоновые задачи
- `alembic/` — миграции

## Запуск
1. Создать venv и установить зависимости:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Скопировать окружение:
   ```bash
   cp .env.example .env
   ```
3. Заполнить `.env`.
4. Применить миграции:
   ```bash
   alembic upgrade head
   ```
5. Запустить:
   ```bash
   python -m bot.main
   ```

## Профили и безопасность
- Публичные профили выбираются только из `profiles` где `enabled=true` и `is_public=true`.
- Служебные/bridge inbound не должны создаваться как публичные профили.
- Роли задаются на уровне `telegram_users.role` и через списки `TELEGRAM_ADMIN_IDS`, `TELEGRAM_SUPPORT_IDS`.

## Systemd
Файл `marzban-bot.service` содержит шаблон для продакшн-деплоя.

