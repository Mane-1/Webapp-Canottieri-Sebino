from __future__ import annotations

from datetime import date
from typing import Optional
from pydantic import BaseModel, condecimal


class MeasurementIn(BaseModel):
    measured_at: Optional[date] = None
    height_cm: Optional[condecimal(ge=0)] = None
    weight_kg: Optional[condecimal(ge=0)] = None
    leg_length_cm: Optional[condecimal(ge=0)] = None
    tibia_length_cm: Optional[condecimal(ge=0)] = None
    arm_length_cm: Optional[condecimal(ge=0)] = None
    torso_height_cm: Optional[condecimal(ge=0)] = None
    wingspan_cm: Optional[condecimal(ge=0)] = None
    notes: Optional[str] = None
