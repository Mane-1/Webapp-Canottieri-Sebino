from __future__ import annotations
from datetime import date, time, timedelta
from typing import TypedDict, Optional

class Occurrence(TypedDict, total=False):
    date: date
    time_start: time
    time_end: time
    is_override: bool
    source_id: int
    coach_id: Optional[int]
    coach_name: Optional[str]

def week_bounds(year: int, isoweek: int) -> tuple[date, date]:
    """Ritorna (lunedi, domenica) della settimana ISO."""
    monday = date.fromisocalendar(year, isoweek, 1)
    sunday = monday + timedelta(days=6)
    return monday, sunday

def expand_occurrences(master, week_range: tuple[date, date]) -> list[Occurrence]:
    """Espande una ricorrenza weekly in memoria (non scrive su DB)."""
    start, end = week_range
    out: list[Occurrence] = []
    if not master.data or not master.time_start or not master.time_end:
        return out
    if start <= master.data <= end:
        out.append({
            "date": master.data,
            "time_start": master.time_start,
            "time_end": master.time_end,
            "is_override": False,
            "source_id": master.id,
        })
    if master.recurrence == "weekly" and master.repeat_until:
        d = master.data
        while d <= master.repeat_until:
            d = d + timedelta(days=7)
            if d > master.repeat_until:
                break
            if start <= d <= end:
                out.append({
                    "date": d,
                    "time_start": master.time_start,
                    "time_end": master.time_end,
                    "is_override": False,
                    "source_id": master.id,
                })
    return out
