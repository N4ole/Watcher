"""Tampon circulaire des logs pour la console « live » du panel web.

Un handler de logging capture chaque enregistrement (toute la sortie console)
dans une file en mémoire, consultable via l'API du panel.
"""
import itertools
import logging
from collections import deque
from threading import Lock

_MAX = 2000
_buffer: deque = deque(maxlen=_MAX)
_lock = Lock()
_counter = itertools.count(1)


class BufferHandler(logging.Handler):
    """Ajoute chaque log formaté au tampon circulaire."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
        except Exception:  # noqa: BLE001
            return
        with _lock:
            _buffer.append(
                {
                    "id": next(_counter),
                    "ts": record.created,
                    "level": record.levelname,
                    "logger": record.name,
                    "msg": msg,
                }
            )


def install(level: int = logging.INFO) -> None:
    """Installe le handler sur le logger racine (idempotent)."""
    root = logging.getLogger()
    if any(isinstance(h, BufferHandler) for h in root.handlers):
        return
    handler = BufferHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    handler.setLevel(level)
    root.addHandler(handler)


def get_since(after_id: int = 0, limit: int = 500) -> list[dict]:
    """Renvoie les enregistrements dont l'id est supérieur à `after_id`."""
    with _lock:
        items = [r for r in _buffer if r["id"] > after_id]
    return items[-limit:]
