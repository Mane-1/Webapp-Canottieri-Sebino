"""SQLAlchemy models for activities management."""

from datetime import date, datetime, timezone
import enum
from decimal import Decimal
from typing import Optional

from sqlalchemy import Column, Integer, String, Text, Date, Time, Enum, Boolean, ForeignKey, Index, CheckConstraint, UniqueConstraint, DECIMAL, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from database import Base


class ActivityState(str, enum.Enum):
    bozza = "bozza"
    da_confermare = "da_confermare"
    confermato = "confermato"
    rimandata = "rimandata"
    in_corso = "in_corso"
    completato = "completato"
    annullato = "annullato"


class PaymentMethod(str, enum.Enum):
    contanti = "contanti"
    carta = "carta"
    bonifico = "bonifico"
    assegno = "assegno"
    altro = "altro"


class PaymentState(str, enum.Enum):
    da_effettuare = "da_effettuare"
    da_verificare = "da_verificare"
    confermato = "confermato"


class ActivityType(Base):
    __tablename__ = "activity_types"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    color = Column(String(7), nullable=False, default="#007BFF")  # Hex color
    is_active = Column(Boolean, default=True)
    
    activities = relationship("Activity", back_populates="activity_type")


class QualificationType(Base):
    __tablename__ = "qualification_types"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    is_active = Column(Boolean, default=True)
    
    user_qualifications = relationship("UserQualification", back_populates="qualification_type")
    requirements = relationship("ActivityRequirement", back_populates="qualification_type")


class Activity(Base):
    __tablename__ = "activities"
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    short_description = Column(Text, nullable=True)
    state = Column(Enum(ActivityState), nullable=False, default=ActivityState.bozza)
    type_id = Column(Integer, ForeignKey("activity_types.id"), nullable=False)
    date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    
    # Informazioni cliente
    customer_name = Column(String(200), nullable=False)
    customer_email = Column(String(200), nullable=True)
    contact_name = Column(String(200), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    contact_email = Column(String(200), nullable=True)
    
    # Partecipanti
    participants_plan = Column(Integer, nullable=False, default=0)
    participants_actual = Column(Integer, nullable=True)
    participants_notes = Column(Text, nullable=True)
    
    # Pagamento
    payment_amount = Column(DECIMAL(10, 2), nullable=True)
    payment_method = Column(Enum(PaymentMethod), nullable=True)
    payment_state = Column(Enum(PaymentState), nullable=False, default=PaymentState.da_effettuare)
    
    # Fatturazione
    billing_name = Column(String(200), nullable=True)
    billing_vat_or_cf = Column(String(50), nullable=True)
    billing_sdi_or_pec = Column(String(200), nullable=True)
    billing_address = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
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
    __tablename__ = "user_qualifications"
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    qualification_type_id = Column(Integer, ForeignKey("qualification_types.id"), primary_key=True)
    
    # Date qualifica
    obtained_date = Column(Date, nullable=False, default=date.today)
    expiry_date = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Relazioni
    user = relationship("User", back_populates="qualifications")
    qualification_type = relationship("QualificationType", back_populates="user_qualifications")
    
    __table_args__ = (
        Index("ix_user_qualifications_user", "user_id"),
        Index("ix_user_qualifications_qualification", "qualification_type_id"),
    )


class ActivityRequirement(Base):
    __tablename__ = "activity_requirements"
    id = Column(Integer, primary_key=True)
    activity_id = Column(Integer, ForeignKey("activities.id"), nullable=False)
    qualification_type_id = Column(Integer, ForeignKey("qualification_types.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    
    # Relazioni
    activity = relationship("Activity", back_populates="requirements")
    qualification_type = relationship("QualificationType", back_populates="requirements")
    assignments = relationship("ActivityAssignment", back_populates="requirement", cascade="all,delete-orphan")
    
    __table_args__ = (
        Index("ix_activity_requirements_activity", "activity_id"),
        Index("ix_activity_requirements_qualification", "qualification_type_id"),
        CheckConstraint("quantity > 0", name="ck_requirement_quantity_positive"),
    )


class ActivityAssignment(Base):
    __tablename__ = "activity_assignments"
    id = Column(Integer, primary_key=True)
    activity_id = Column(Integer, ForeignKey("activities.id"), nullable=False)
    requirement_id = Column(Integer, ForeignKey("activity_requirements.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role_label = Column(String(100), nullable=True)  # Etichetta personalizzata del ruolo
    hours = Column(DECIMAL(5, 2), nullable=True)  # Ore assegnate (es. 3.5)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relazioni
    activity = relationship("Activity", back_populates="assignments")
    requirement = relationship("ActivityRequirement", back_populates="assignments")
    user = relationship("User", back_populates="activity_assignments")
    
    __table_args__ = (
        Index("ix_activity_assignments_activity", "activity_id"),
        Index("ix_activity_assignments_requirement", "requirement_id"),
        Index("ix_activity_assignments_user", "user_id"),
        UniqueConstraint("activity_id", "requirement_id", "user_id", name="uq_activity_assignment"),
    )


# Placeholder per Fase 2
class ActivityAudit(Base):
    __tablename__ = "activity_audits"
    id = Column(Integer, primary_key=True)
    activity_id = Column(Integer, ForeignKey("activities.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(50), nullable=False)  # create, update, delete
    changes = Column(Text, nullable=True)  # JSON o testo descrittivo
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relazioni
    activity = relationship("Activity")
    user = relationship("User")
    
    __table_args__ = (
        Index("ix_activity_audits_activity", "activity_id"),
        Index("ix_activity_audits_user", "user_id"),
        Index("ix_activity_audits_timestamp", "timestamp"),
    )
