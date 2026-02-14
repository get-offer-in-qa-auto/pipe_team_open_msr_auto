from __future__ import annotations

from datetime import datetime, timezone, timedelta


def iso_utc(dt: datetime) -> str:
    """Return ISO-8601 UTC string with milliseconds and 'Z' suffix."""
    return dt.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def now_iso_utc() -> str:
    """Shortcut for current time in ISO-UTC format."""
    return iso_utc(datetime.now(timezone.utc))


def future_iso_utc() -> str:
    """Current time +1 hour in ISO-UTC format."""
    return iso_utc(datetime.now(timezone.utc) + timedelta(hours=1))


def past_iso_utc(hours: int = 0, minutes: int = 0) -> str:
    return iso_utc(datetime.now(timezone.utc) - timedelta(hours=hours, minutes=minutes))