"""Journalisation structurée (JSON) avec masquage des secrets."""

import json
import logging
import re
import sys
from datetime import UTC, datetime
from typing import Any

_SENSITIVE_KEY = re.compile(r"(pass(word)?|secret|token|api[_-]?key|cookie|authorization)", re.I)
# Masque les identifiants dans les URL de connexion : scheme://user:password@host
_URL_CREDENTIALS = re.compile(r"(\w+://[^:/\s]+:)[^@\s]+(@)")
_INLINE_SECRET = re.compile(r"((?:password|secret|token|api[_-]?key)\s*[=:]\s*)([^\s,;&]+)", re.I)

REDACTED = "***"


def redact(text: str) -> str:
    text = _URL_CREDENTIALS.sub(rf"\1{REDACTED}\2", text)
    return _INLINE_SECRET.sub(rf"\1{REDACTED}", text)


def redact_mapping(data: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in data.items():
        if _SENSITIVE_KEY.search(key):
            out[key] = REDACTED
        elif isinstance(value, dict):
            out[key] = redact_mapping(value)
        elif isinstance(value, str):
            out[key] = redact(value)
        else:
            out[key] = value
    return out


_RESERVED = set(vars(logging.makeLogRecord({})).keys()) | {"message", "asctime"}


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": redact(record.getMessage()),
        }
        extra = {k: v for k, v in vars(record).items() if k not in _RESERVED}
        if extra:
            payload.update(redact_mapping(extra))
        if record.exc_info:
            payload["exc"] = redact(self.formatException(record.exc_info))
        return json.dumps(payload, ensure_ascii=False, default=str)


def configure_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level)
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        lg = logging.getLogger(name)
        lg.handlers[:] = []
        lg.propagate = True
