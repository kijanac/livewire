import json
import logging
import sys
import traceback
from contextvars import ContextVar
from datetime import datetime, timezone

from app.config import settings

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)

_SERVICE_NAME = "livewire-backend"

_LEVEL_MAP = {
    "DEBUG": "debug",
    "INFO": "info",
    "WARNING": "warn",
    "ERROR": "error",
    "CRITICAL": "error",
}

_RESERVED_RECORD_ATTRS = frozenset({
    "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
    "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
    "created", "msecs", "relativeCreated", "thread", "threadName",
    "processName", "process", "message", "asctime", "taskName",
})


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(record.created, tz=timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%S.%f"
        )[:-3] + "Z"

        payload: dict = {
            "timestamp": timestamp,
            "level": _LEVEL_MAP.get(record.levelname, record.levelname.lower()),
            "event": record.getMessage(),
            "service": _SERVICE_NAME,
            "environment": getattr(settings, "ENVIRONMENT", "dev"),
            "request_id": request_id_var.get(),
        }

        for key, value in record.__dict__.items():
            if key in _RESERVED_RECORD_ATTRS or key.startswith("_"):
                continue
            if key in payload:
                continue
            payload[key] = _safe_value(value)

        if record.exc_info:
            exc_type, exc_value, exc_tb = record.exc_info
            payload["error_type"] = exc_type.__name__ if exc_type else None
            payload["error_message"] = str(exc_value) if exc_value else None
            payload["traceback"] = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))

        return json.dumps(payload, default=_safe_value, ensure_ascii=False)


def _safe_value(value: object) -> object:
    if isinstance(value, (str, int, float, bool, type(None))):
        return value
    if isinstance(value, (list, tuple)):
        return [_safe_value(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _safe_value(v) for k, v in value.items()}
    return str(value)


def setup_logging(level: str = "INFO") -> None:
    formatter = JsonFormatter()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

    for uv_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        uv_logger = logging.getLogger(uv_name)
        uv_logger.handlers.clear()
        uv_logger.addHandler(handler)
        uv_logger.setLevel(level)
        uv_logger.propagate = False
