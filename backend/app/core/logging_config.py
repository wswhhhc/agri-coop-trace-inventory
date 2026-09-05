from __future__ import annotations

import logging
import sys
from logging.handlers import TimedRotatingFileHandler

from app.core.config import Settings, get_settings

LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
_MANAGED_ATTRIBUTE = "_agri_managed"


def _mark_managed(handler: logging.Handler) -> logging.Handler:
    setattr(handler, _MANAGED_ATTRIBUTE, True)
    return handler


def _remove_managed_handlers(logger: logging.Logger) -> None:
    for handler in logger.handlers[:]:
        if getattr(handler, _MANAGED_ATTRIBUTE, False):
            logger.removeHandler(handler)
            handler.close()


def configure_logging(settings: Settings | None = None) -> None:
    """配置应用控制台和按天轮转的 UTF-8 文件日志。"""
    settings = settings or get_settings()
    settings.log_dir_path.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    console_handler = _mark_managed(logging.StreamHandler(sys.stdout))
    console_handler.setFormatter(formatter)

    file_handler = _mark_managed(
        TimedRotatingFileHandler(
            settings.log_dir_path / "app.log",
            when="midnight",
            interval=1,
            backupCount=settings.log_backup_count,
            encoding="utf-8",
        )
    )
    file_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    _remove_managed_handlers(root_logger)
    root_logger.setLevel(settings.log_level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Uvicorn 默认给这些 logger 配置独立 handler，统一交给 root logger，避免漏写或重复输出。
    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        named_logger = logging.getLogger(logger_name)
        for handler in named_logger.handlers[:]:
            named_logger.removeHandler(handler)
            handler.close()
        named_logger.propagate = True


__all__ = ["configure_logging"]
