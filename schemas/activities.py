"""Pydantic schemas for activities management."""

from datetime import date, time, datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, validator


# --- SCHEMI BASE ---

class ActivityTypeRead(BaseModel):
    """Schema per la lettura di un tipo di attività."""
    id: int
    name: str
    color: Optional[str] = None
    is_active: bool
    
    class Config:
        from_attributes = True


class QualificationTypeRead(BaseModel):
    """Schema per la lettura di un tipo di qualifica."""
    id: int
    name: str
    is_active: bool
    
    class Config:
        from_attributes = True


# --- SCHEMI PER I REQUISITI ---

class ActivityRequirementCreate(BaseModel):
    """Schema per la creazione di un requisito di attività."""
    qualification_type_id: int
    quantity: int = Field(..., ge=1)
    
    @validator('quantity')
    def validate_quantity(cls, v):
        if v < 1:
            raise ValueError('La quantità deve essere almeno 1')
        return v


class ActivityRequirementUpdate(BaseModel):
    """Schema per l'aggiornamento di un requisito di attività."""
    quantity: int = Field(..., ge=1)
    
    @validator('quantity')
    def validate_quantity(cls, v):
        if v < 1:
            raise ValueError('La quantità deve essere almeno 1')
        return v


class ActivityRequirementRead(BaseModel):
    """Schema per la lettura di un requisito di attività."""
    id: int
    qualification_type_id: int
    qualification_type: QualificationTypeRead
    quantity: int
    assigned_count: int = 0  # Calcolato dinamicamente
    
    class Config:
        from_attributes = True


# --- SCHEMI PER LE ASSEGNAZIONI ---

class AssignmentCreate(BaseModel):
    """Schema per la creazione di un'assegnazione."""
    activity_id: int
    requirement_id: int
    user_id: int
    role_label: Optional[str] = None
    hours: Optional[float] = None


class AssignmentRead(BaseModel):
    """Schema per la lettura di un'assegnazione."""
    id: int
    activity_id: int
    requirement_id: int
    user_id: int
    user_name: str  # Nome completo dell'utente
    role_label: Optional[str] = None
    hours: Optional[float] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# --- SCHEMI PER LE ATTIVITÀ ---

class ActivityCreate(BaseModel):
    """Schema per la creazione di un'attività."""
    title: str = Field(..., min_length=1, max_length=200)
    short_description: Optional[str] = None
    state: str = "bozza"  # Default
    type_id: int
    date: date
    start_time: time
    end_time: time
    
    # Cliente
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    
    # Contatti
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    
    # Partecipanti
    participants_plan: Optional[int] = Field(None, ge=0)
    participants_actual: Optional[int] = Field(None, ge=0)
    participants_notes: Optional[str] = None
    
    # Pagamento
    payment_amount: Optional[Decimal] = Field(None, ge=0)
    payment_method: Optional[str] = None
    payment_state: str = "da_effettuare"  # Default
    
    # Fatturazione
    billing_name: Optional[str] = None
    billing_vat_or_cf: Optional[str] = None
    billing_sdi_or_pec: Optional[str] = None
    billing_address: Optional[str] = None
    
    @validator('end_time')
    def validate_time_order(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('L\'ora di fine deve essere successiva all\'ora di inizio')
        return v


class ActivityUpdate(BaseModel):
    """Schema per l'aggiornamento di un'attività."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    short_description: Optional[str] = None
    state: Optional[str] = None
    type_id: Optional[int] = None
    date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    
    # Cliente
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    
    # Contatti
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    
    # Partecipanti
    participants_plan: Optional[int] = Field(None, ge=0)
    participants_actual: Optional[int] = Field(None, ge=0)
    participants_notes: Optional[str] = None
    
    # Pagamento
    payment_amount: Optional[Decimal] = Field(None, ge=0)
    payment_method: Optional[str] = None
    payment_state: Optional[str] = None
    
    # Fatturazione
    billing_name: Optional[str] = None
    billing_vat_or_cf: Optional[str] = None
    billing_sdi_or_pec: Optional[str] = None
    billing_address: Optional[str] = None
    
    @validator('end_time')
    def validate_time_order(cls, v, values):
        if v is not None and 'start_time' in values and values['start_time'] is not None:
            if v <= values['start_time']:
                raise ValueError('L\'ora di fine deve essere successiva all\'ora di inizio')
        return v


class ActivityRead(BaseModel):
    """Schema per la lettura di un'attività."""
    id: int
    title: str
    short_description: Optional[str] = None
    state: str
    type_id: int
    activity_type: ActivityTypeRead
    date: date
    start_time: time
    end_time: time
    
    # Cliente
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    
    # Contatti
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    
    # Partecipanti
    participants_plan: Optional[int] = None
    participants_actual: Optional[int] = None
    participants_notes: Optional[str] = None
    
    # Pagamento
    payment_amount: Optional[Decimal] = None
    payment_method: Optional[str] = None
    payment_state: str
    
    # Fatturazione
    billing_name: Optional[str] = None
    billing_vat_or_cf: Optional[str] = None
    billing_sdi_or_pec: Optional[str] = None
    billing_address: Optional[str] = None
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    
    # Calcoli dinamici
    coverage_percentage: int = 0  # Percentuale di copertura (0-100)
    total_required: int = 0       # Totale requisiti
    total_assigned: int = 0       # Totale assegnati
    
    # Relazioni
    requirements: List[ActivityRequirementRead] = []
    assignments: List[AssignmentRead] = []
    
    class Config:
        from_attributes = True


# --- SCHEMI PER I FILTRI ---

class ActivityFilter(BaseModel):
    """Schema per i filtri delle attività."""
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    type_ids: Optional[List[int]] = None
    states: Optional[List[str]] = None
    payment_states: Optional[List[str]] = None
    text: Optional[str] = None
    user_id: Optional[int] = None  # Per filtrare per utente assegnato
    
    @validator('date_to')
    def validate_date_range(cls, v, values):
        if v is not None and 'date_from' in values and values['date_from'] is not None:
            if v < values['date_from']:
                raise ValueError('La data di fine deve essere successiva alla data di inizio')
        return v


# --- SCHEMI PER LE ESTRAZIONI ---

class ExtractionRow(BaseModel):
    """Schema per una riga di estrazione ore."""
    date: date
    activity_title: str
    qualification_name: str
    role_label: Optional[str] = None
    hours: float
    activity_id: int


class ExtractionFilter(BaseModel):
    """Schema per i filtri delle estrazioni."""
    user_id: Optional[int] = None
    month: Optional[int] = Field(None, ge=1, le=12)
    year: Optional[int] = Field(None, ge=2020, le=2030)


# --- SCHEMI PER I PAGAMENTI ---

class PaymentKPI(BaseModel):
    """Schema per i KPI dei pagamenti."""
    total_activities: int
    total_amount: Decimal
    pending_count: int
    pending_amount: Decimal
    confirmed_count: int
    confirmed_amount: Decimal


class PaymentSummary(BaseModel):
    """Schema per il riepilogo dei pagamenti."""
    kpi: PaymentKPI
    activities: List[ActivityRead]


# --- SCHEMI PER L'AUTOCANDIDATURA ---

class SelfAssignRequest(BaseModel):
    """Schema per la richiesta di autocandidatura."""
    activity_id: int
    requirement_id: Optional[int] = None  # Se non specificato, viene scelto automaticamente


class SelfAssignResponse(BaseModel):
    """Schema per la risposta all'autocandidatura."""
    success: bool
    message: str
    assignment: Optional[AssignmentRead] = None
    requirement_id: Optional[int] = None
