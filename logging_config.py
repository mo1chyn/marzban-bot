import logging
from logging.handlers import RotatingFileHandler


def setup_logging(level: str = "INFO") -> None:
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")

    app_handler = RotatingFileHandler("app.log", maxBytes=2 * 1024 * 1024, backupCount=3, encoding="utf-8")
    app_handler.setLevel(getattr(logging, level.upper(), logging.INFO))
    app_handler.setFormatter(formatter)

    error_handler = RotatingFileHandler("error.log", maxBytes=2 * 1024 * 1024, backupCount=3, encoding="utf-8")
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, level.upper(), logging.INFO))
    console_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    root.handlers.clear()
    root.addHandler(app_handler)
    root.addHandler(error_handler)
    root.addHandler(console_handler)
