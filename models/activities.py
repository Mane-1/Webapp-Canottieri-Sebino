"""SQLAlchemy models for activities management."""

from datetime import date, datetime, timezone
import enum
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    Time,
    Text,
    ForeignKey,
    Float,
    Boolean,
    Index,
    CheckConstraint,
    UniqueConstraint,
    Enum,
    DateTime,
    Numeric,
)
from sqlalchemy.orm import relationship, backref
from database import Base


class ActivityState(enum.Enum):
    """Stati possibili per un'attività."""
    bozza = "bozza"
    da_confermare = "da_confermare"
    confermata = "confermata"
    rimandata = "rimandata"
    annullata = "annullata"
    completata = "completata"


class PaymentMethod(enum.Enum):
    """Metodi di pagamento disponibili."""
    contanti = "contanti"
    carta = "carta"
    bonifico = "bonifico"
    assegno = "assegno"
    voucher = "voucher"
    altro = "altro"


class PaymentState(enum.Enum):
    """Stati del pagamento."""
    da_effettuare = "da_effettuare"
    da_verificare = "da_verificare"
    confermato = "confermato"


class ActivityType(Base):
    """Tipi di attività disponibili."""
    __tablename__ = "activity_types"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    color = Column(String(7), nullable=True)  # Hex color code
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relazioni
    activities = relationship("Activity", back_populates="activity_type")
    
    __table_args__ = (
        Index("ix_activity_types_active", "is_active"),
    )


class QualificationType(Base):
    """Tipi di qualifiche disponibili."""
    __tablename__ = "qualification_types"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relazioni
    user_qualifications = relationship("UserQualification", back_populates="qualification_type")
    activity_requirements = relationship("ActivityRequirement", back_populates="qualification_type")
    
    __table_args__ = (
        Index("ix_qualification_types_active", "is_active"),
    )


class Activity(Base):
    """Attività principali."""
    __tablename__ = "activities"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    short_description = Column(Text, nullable=True)
    state = Column(Enum(ActivityState), nullable=False, default=ActivityState.bozza, index=True)
    
    # Tipo e date
    type_id = Column(Integer, ForeignKey("activity_types.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    
    # Cliente
    customer_name = Column(String(200), nullable=True)
    customer_email = Column(String(200), nullable=True)
    
    # Contatti
    contact_name = Column(String(200), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    contact_email = Column(String(200), nullable=True)
    
    # Partecipanti
    participants_plan = Column(Integer, nullable=True)
    participants_actual = Column(Integer, nullable=True)
    participants_notes = Column(Text, nullable=True)
    
    # Pagamento
    payment_amount = Column(Numeric(10, 2), nullable=True)
    payment_method = Column(Enum(PaymentMethod), nullable=True)
    payment_state = Column(Enum(PaymentState), nullable=False, default=PaymentState.da_effettuare, index=True)
    
    # Fatturazione
    billing_name = Column(String(200), nullable=True)
    billing_vat_or_cf = Column(String(50), nullable=True)
    billing_sdi_or_pec = Column(String(200), nullable=True)
    billing_address = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relazioni
    activity_type = relationship("ActivityType", back_populates="activities")
    requirements = relationship("ActivityRequirement", back_populates="activity", cascade="all,delete-orphan")
    assignments = relationship("ActivityAssignment", back_populates="activity", cascade="all,delete-orphan")
    
    __table_args__ = (
        Index("ix_activities_date", "date"),
        Index("ix_activities_type_date", "type_id", "date"),
        Index("ix_activities_state_date", "state", "date"),
        Index("ix_activities_payment_state", "payment_state"),
        CheckConstraint("end_time > start_time", name="ck_activity_time_order"),
    )


class UserQualification(Base):
    """Qualifiche assegnate agli utenti."""
    __tablename__ = "user_qualifications"
    
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    qualification_type_id = Column(Integer, ForeignKey("qualification_types.id", ondelete="CASCADE"), primary_key=True)
    
    # Relazioni
    user = relationship("User", backref=backref("qualifications", cascade="all,delete-orphan"))
    qualification_type = relationship("QualificationType", back_populates="user_qualifications")
    
    __table_args__ = (
        Index("ix_user_qualifications_user", "user_id"),
        Index("ix_user_qualifications_type", "qualification_type_id"),
    )


class ActivityRequirement(Base):
    """Requisiti per un'attività (quante persone con quale qualifica)."""
    __tablename__ = "activity_requirements"
    
    id = Column(Integer, primary_key=True, index=True)
    activity_id = Column(Integer, ForeignKey("activities.id", ondelete="CASCADE"), nullable=False, index=True)
    qualification_type_id = Column(Integer, ForeignKey("qualification_types.id", ondelete="CASCADE"), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    
    # Relazioni
    activity = relationship("Activity", back_populates="requirements")
    qualification_type = relationship("QualificationType", back_populates="activity_requirements")
    assignments = relationship("ActivityAssignment", back_populates="requirement", cascade="all,delete-orphan")
    
    __table_args__ = (
        Index("ix_activity_requirements_activity", "activity_id"),
        Index("ix_activity_requirements_qualification", "qualification_type_id"),
        CheckConstraint("quantity >= 1", name="ck_requirement_quantity_positive"),
    )


class ActivityAssignment(Base):
    """Assegnazioni di utenti ai requisiti di un'attività."""
    __tablename__ = "activity_assignments"
    
    id = Column(Integer, primary_key=True, index=True)
    activity_id = Column(Integer, ForeignKey("activities.id", ondelete="CASCADE"), nullable=False, index=True)
    requirement_id = Column(Integer, ForeignKey("activity_requirements.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Dettagli dell'assegnazione
    role_label = Column(String(100), nullable=True)  # Testo libero per il ruolo
    hours = Column(Float, nullable=True)  # Ore effettive (default calcolato da start/end)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    
    # Relazioni
    activity = relationship("Activity", back_populates="assignments")
    requirement = relationship("ActivityRequirement", back_populates="assignments")
    user = relationship("User", backref=backref("activity_assignments", cascade="all,delete-orphan"))
    
    __table_args__ = (
        Index("ix_activity_assignments_activity", "activity_id"),
        Index("ix_activity_assignments_requirement", "requirement_id"),
        Index("ix_activity_assignments_user", "user_id"),
        UniqueConstraint("activity_id", "requirement_id", "user_id", name="uq_assignment_unique"),
    )


# Modelli facoltativi per Fase 2 (solo strutture/commenti)
class ActivityAudit(Base):
    """Log delle modifiche alle attività (FASE 2)."""
    __tablename__ = "activity_audits"
    
    id = Column(Integer, primary_key=True, index=True)
    activity_id = Column(Integer, ForeignKey("activities.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    field = Column(String(100), nullable=False)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    timestamp = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    
    # Relazioni
    activity = relationship("Activity")
    user = relationship("User")
    
    __table_args__ = (
        Index("ix_activity_audits_activity", "activity_id"),
        Index("ix_activity_audits_user", "user_id"),
        Index("ix_activity_audits_timestamp", "timestamp"),
    )


# Estensione del modello User esistente per includere le nuove relazioni
# Questo verrà aggiunto al modello User esistente in models.py
def extend_user_model(User):
    """Estende il modello User esistente con le nuove relazioni per le attività."""
    # Le relazioni sono già definite nei modelli sopra tramite backref
    # User.qualifications -> UserQualification[]
    # User.activity_assignments -> ActivityAssignment[]
    pass
