from __future__ import annotations

from datetime import date, datetime
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


class AthleteUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    date_of_birth: Optional[date] = None
    tax_code: Optional[str] = None
    enrollment_year: Optional[int] = None
    membership_date: Optional[date] = None
    certificate_expiration: Optional[date] = None
    address: Optional[str] = None
    manual_category: Optional[str] = None


class EquipaggioCreate(BaseModel):
    nome: str
    barca_id: int
    capovoga_id: int
    secondo_id: Optional[int] = None
    terzo_id: Optional[int] = None
    quarto_id: Optional[int] = None
    quinto_id: Optional[int] = None
    sesto_id: Optional[int] = None
    settimo_id: Optional[int] = None
    prodiere_id: Optional[int] = None
    timoniere_id: Optional[int] = None
    note: Optional[str] = None


class EquipaggioUpdate(BaseModel):
    nome: Optional[str] = None
    capovoga_id: Optional[int] = None
    secondo_id: Optional[int] = None
    terzo_id: Optional[int] = None
    quarto_id: Optional[int] = None
    quinto_id: Optional[int] = None
    sesto_id: Optional[int] = None
    settimo_id: Optional[int] = None
    prodiere_id: Optional[int] = None
    timoniere_id: Optional[int] = None
    note: Optional[str] = None


class EquipaggioResponse(BaseModel):
    id: int
    nome: str
    barca_id: int
    capovoga_id: int
    secondo_id: Optional[int] = None
    terzo_id: Optional[int] = None
    quarto_id: Optional[int] = None
    quinto_id: Optional[int] = None
    sesto_id: Optional[int] = None
    settimo_id: Optional[int] = None
    prodiere_id: Optional[int] = None
    timoniere_id: Optional[int] = None
    note: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    # Relazioni
    capovoga: Optional[AthleteResponse] = None
    secondo: Optional[AthleteResponse] = None
    terzo: Optional[AthleteResponse] = None
    quarto: Optional[AthleteResponse] = None
    quinto: Optional[AthleteResponse] = None
    sesto: Optional[AthleteResponse] = None
    settimo: Optional[AthleteResponse] = None
    prodiere: Optional[AthleteResponse] = None
    timoniere: Optional[AthleteResponse] = None

    class Config:
        from_attributes = True
