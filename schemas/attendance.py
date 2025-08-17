from __future__ import annotations

from typing import List, Optional, Literal
from pydantic import BaseModel


class ToggleAttendanceIn(BaseModel):
    new_status: Literal["present", "absent"]


class SetAttendanceIn(BaseModel):
    status: Literal["present", "absent"]
    reason: Optional[str] = None


class AttendanceBulkItem(BaseModel):
    athlete_id: int
    status: Literal["present", "absent"]


class AttendanceBulkIn(BaseModel):
    items: List[AttendanceBulkItem]
    reason: Optional[str] = None
