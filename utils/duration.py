"""Analyse de durées courtes et combinables : 30s, 5m, 2h, 1d, 1h30m."""
import re
from datetime import timedelta

_UNITS = {"s": 1, "m": 60, "h": 3600, "d": 86400, "j": 86400}
_RE = re.compile(r"(\d+)\s*([smhdj])", re.IGNORECASE)


def parse_duration(text: str) -> timedelta | None:
    """Convertit '1h30m' / '5m' / '30s' en timedelta. None si invalide."""
    matches = _RE.findall(text)
    if not matches:
        return None
    total = sum(int(value) * _UNITS[unit.lower()] for value, unit in matches)
    if total <= 0:
        return None
    return timedelta(seconds=total)


def human(delta: timedelta) -> str:
    """Formate une durée en 'Xj Yh Zm Ws'."""
    total = int(delta.total_seconds())
    days, rem = divmod(total, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, seconds = divmod(rem, 60)
    parts = []
    if days:
        parts.append(f"{days}j")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if seconds or not parts:
        parts.append(f"{seconds}s")
    return " ".join(parts)
