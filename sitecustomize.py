"""Test environment compatibility helpers."""

from datetime import timezone
import datetime as _datetime

# Python <3.11 does not expose datetime.UTC; provide a backport for tests.
if not hasattr(_datetime, "UTC"):
    _datetime.UTC = timezone.utc  # type: ignore[attr-defined]
