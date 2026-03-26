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
Файл `marzban-bot.service` содержит готовый пример юнита для продакшн-деплоя.

### Быстрый чек-лист для ошибки `status=203/EXEC`
Если в `journalctl` видите:
- `Failed at step EXEC`
- `No such file or directory`
- `status=203/EXEC`

значит путь в `ExecStart` неверный (или виртуальное окружение не создано).

Проверьте:
1. Папка проекта и окружения реально существуют:
   ```bash
   ls -la /opt/marzban-bot
   ls -la /opt/marzban-bot/.venv/bin/python
   ```
2. В юните используется **тот же путь**, что и в системе:
   - правильно для этого репозитория: `/opt/marzban-bot/.venv/bin/python`
   - частая ошибка: `/path/to/.../venv/bin/python` (шаблонный путь) или `venv` вместо `.venv`
3. Юнит перезагружен после изменений:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl restart marzban-bot
   sudo systemctl status marzban-bot --no-pager -l
   ```

### Эталонный unit-файл
```ini
[Unit]
Description=Marzban Telegram Bot
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/marzban-bot
EnvironmentFile=/opt/marzban-bot/.env
ExecStart=/opt/marzban-bot/.venv/bin/python -m bot.main
Restart=always
RestartSec=5
User=marzbanbot
Group=marzbanbot

[Install]
WantedBy=multi-user.target
```
