from __future__ import annotations

from datetime import datetime, timezone


def iso_utc(dt: datetime) -> str:
    """Return ISO-8601 UTC string with milliseconds and 'Z' suffix."""
    return dt.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def now_iso_utc() -> str:
    """Shortcut for current time in ISO-UTC format."""
    return iso_utc(datetime.now(timezone.utc))