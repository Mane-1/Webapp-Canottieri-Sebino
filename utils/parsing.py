from __future__ import annotations
from typing import Optional


def to_float(value: Optional[str]) -> Optional[float]:
    """Convert a string to float if possible, otherwise return ``None``."""
    try:
        return float(value) if value and value.strip() else None
    except ValueError:
        return None
