"""SQLAlchemy models for the application."""

from datetime import date, datetime
from typing import Tuple
import enum

from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    Time,
    Text,
    Table,
    ForeignKey,
    Float,
    Boolean,
    Index,
    CheckConstraint,
    UniqueConstraint,
    Enum,
    DateTime,
)
from sqlalchemy.orm import relationship, object_session, backref
from sqlalchemy.orm.attributes import flag_modified
from database import Base

# --- TABELLE DI ASSOCIAZIONE (MOLTI-A-MOLTI) ---

allenamento_categoria_association = Table(
    'allenamento_categoria_association', Base.metadata,
    Column('allenamento_id', Integer, ForeignKey('allenamenti.id'), primary_key=True),
    Column('categoria_id', Integer, ForeignKey('categorie.id'), primary_key=True)
)

user_roles = Table(
    'user_roles', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True)
)

barca_atleti_association = Table(
    'barca_atleti_association', Base.metadata,
    Column('barca_id', Integer, ForeignKey('barche.id'), primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True)
)

user_tags = Table(
    'user_tags', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True)
)

allenamento_coach_association = Table(
    'allenamento_coach_association', Base.metadata,
    Column('allenamento_id', Integer, ForeignKey('allenamenti.id'), primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True)
)


# --- MODELLI DELLE TABELLE PRINCIPALI ---

class Categoria(Base):
    __tablename__ = "categorie"
    id = Column(Integer, primary_key=True)
    nome = Column(String, unique=True, nullable=False)
    eta_min = Column(Integer, nullable=False)
    eta_max = Column(Integer, nullable=False)
    ordine = Column(Integer, default=0)
    # raggruppamento logico (es. "Under 14", "Over 14", "Master")
    macro_group = Column(String, nullable=True, index=True)
    allenamenti = relationship(
        "Allenamento", secondary=allenamento_categoria_association, back_populates="categories"
    )


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True)
    phone_number = Column(String)
    date_of_birth = Column(Date)
    tax_code = Column(String, unique=True)
    enrollment_year = Column(Integer)
    membership_date = Column(Date)
    certificate_expiration = Column(Date)
    address = Column(String)
    manual_category = Column(String, nullable=True)
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    tags = relationship("Tag", secondary=user_tags, back_populates="users")
    barche_assegnate = relationship("Barca", secondary=barca_atleti_association, back_populates="atleti_assegnati")
    schede_pesi = relationship("SchedaPesi", back_populates="atleta")
    turni = relationship("Turno", back_populates="user")
    availabilities = relationship("TrainerAvailability", back_populates="user")
    allenamenti_seguiti = relationship("Allenamento", secondary=allenamento_coach_association, back_populates="coaches")

    @property
    def age(self) -> int:
        if not self.date_of_birth: return 0
        today = date.today()
        return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))

    @property
    def solar_age(self) -> int:
        if not self.date_of_birth: return 0
        return date.today().year - self.date_of_birth.year

    @property
    def is_admin(self) -> bool:
        return any(role.name == "admin" for role in self.roles)

    @property
    def is_allenatore(self) -> bool:
        return any(role.name == "allenatore" for role in self.roles)

    @property
    def is_atleta(self) -> bool:
        return any(role.name == "atleta" for role in self.roles)

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def _category_obj(self) -> Categoria | None:
        if not self.is_atleta or not self.date_of_birth: return None
        db_session = object_session(self)
        if not db_session: return None
        age = self.solar_age
        return db_session.query(Categoria).filter(Categoria.eta_min <= age, Categoria.eta_max >= age).first()

    @property
    def category(self) -> str:
        """Return the user's category name.

        If ``manual_category`` is populated we verify that such category exists
        in the database.  This prevents typos from returning an inconsistent
        value.  When the manual category is invalid we gracefully fall back to
        the automatically calculated one so that the application never
        crashes and always shows a meaningful category.
        """
        if self.manual_category:
            db_session = object_session(self)
            if db_session and db_session.query(Categoria).filter_by(nome=self.manual_category).first():
                return self.manual_category
        categoria_obj = self._category_obj
        return categoria_obj.nome if categoria_obj else "N/D"


class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    users = relationship("User", secondary=user_roles, back_populates="roles")


class Tag(Base):
    __tablename__ = 'tags'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    category = Column(String, default="Generale")
    users = relationship("User", secondary=user_tags, back_populates="tags")


class Barca(Base):
    __tablename__ = "barche"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    tipo = Column(String, index=True, nullable=False)
    costruttore = Column(String, nullable=True)
    anno = Column(Integer, nullable=True)
    remi_assegnati = Column(String, nullable=True)
    atleti_assegnati = relationship("User", secondary=barca_atleti_association, back_populates="barche_assegnate")
    in_manutenzione = Column(Boolean, default=False, nullable=False)
    fuori_uso = Column(Boolean, default=False, nullable=False)
    in_prestito = Column(Boolean, default=False, nullable=False)
    in_trasferta = Column(Boolean, default=False, nullable=False)
    disponibile_dal = Column(Date, nullable=True)
    lunghezza_puntapiedi = Column(Float, nullable=True)
    altezza_puntapiedi = Column(Float, nullable=True)
    apertura_totale = Column(Float, nullable=True)
    altezza_scalmo_sx = Column(Float, nullable=True)
    altezza_scalmo_dx = Column(Float, nullable=True)
    semiapertura_sx = Column(Float, nullable=True)
    semiapertura_dx = Column(Float, nullable=True)
    appruamento_appoppamento = Column(Float, nullable=True)
    gradi_attacco = Column(Float, nullable=True)
    gradi_finale = Column(Float, nullable=True)
    boccola_sx_sopra = Column(String, nullable=True)
    boccola_dx_sopra = Column(String, nullable=True)
    rondelle_sx = Column(String, nullable=True)
    rondelle_dx = Column(String, nullable=True)
    altezza_carrello = Column(Float, nullable=True)
    avanzamento_guide = Column(Float, nullable=True)

    @property
    def status(self) -> Tuple[str, str]:
        if self.fuori_uso: return "Fuori uso", "bg-danger"
        if self.in_manutenzione: return "In manutenzione", "bg-warning text-dark"
        if self.in_prestito: return "In prestito", "bg-info text-dark"
        if self.in_trasferta: return "In trasferta", "bg-purple"
        return "In uso", "bg-success"

class EsercizioPesi(Base):
    __tablename__ = "esercizi_pesi"
    id = Column(Integer, primary_key=True)
    ordine = Column(Integer, nullable=False)
    nome = Column(String, nullable=False, unique=True)
    schede = relationship("SchedaPesi", back_populates="esercizio", cascade="all, delete-orphan")


class SchedaPesi(Base):
    __tablename__ = "schede_pesi"
    id = Column(Integer, primary_key=True)
    atleta_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    esercizio_id = Column(Integer, ForeignKey('esercizi_pesi.id'), nullable=False)
    massimale = Column(Float)
    carico_5_rep = Column(Float)
    carico_7_rep = Column(Float)
    carico_10_rep = Column(Float)
    carico_20_rep = Column(Float)
    atleta = relationship("User", back_populates="schede_pesi")
    esercizio = relationship("EsercizioPesi", back_populates="schede")


class Allenamento(Base):
    __tablename__ = "allenamenti"
    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String, nullable=False)
    descrizione = Column(String)
    data = Column(Date, nullable=False)
    orario = Column(String)
    time_start = Column(Time, nullable=True)
    time_end = Column(Time, nullable=True)
    recurrence = Column(String(20), nullable=True)
    repeat_until = Column(Date, nullable=True)
    barca_id = Column(ForeignKey('barche.id'), nullable=True)
    coach_id = Column(ForeignKey('users.id'), nullable=True)
    recurrence_id = Column(String, index=True, nullable=True)
    categories = relationship(
        "Categoria", secondary=allenamento_categoria_association, back_populates="allenamenti"
    )
    coaches = relationship(
        "User", secondary=allenamento_coach_association, back_populates="allenamenti_seguiti"
    )
    barca = relationship("Barca", lazy="selectin")
    coach = relationship("User", foreign_keys=[coach_id], lazy="selectin")


Index("idx_allenamenti_date", Allenamento.data)
Index("idx_allenamenti_barca", Allenamento.barca_id)
Index("idx_allenamenti_coach", Allenamento.coach_id)


class Turno(Base):
    __tablename__ = "turni"
    id = Column(Integer, primary_key=True, index=True)
    data = Column(Date, nullable=False, index=True)
    fascia_oraria = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    user = relationship("User", back_populates="turni")


class TrainerAvailability(Base):
    __tablename__ = "trainer_availabilities"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    turno_id = Column(Integer, ForeignKey('turni.id'), nullable=False, index=True)
    available = Column(Boolean, default=True)
    user = relationship("User", back_populates="availabilities")
    turno = relationship("Turno")
    __table_args__ = (
        UniqueConstraint('user_id', 'turno_id', name='uq_user_turno_availability'),
    )


class AttendanceStatus(enum.Enum):
    present = "present"
    absent = "absent"


class AttendanceSource(enum.Enum):
    system = "system"
    athlete = "athlete"
    coach = "coach"


class Attendance(Base):
    __tablename__ = "attendances"

    id = Column(Integer, primary_key=True)
    training_id = Column(Integer, ForeignKey("allenamenti.id", ondelete="CASCADE"), nullable=False)
    athlete_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status = Column(Enum(AttendanceStatus), nullable=False, default=AttendanceStatus.present)
    source = Column(Enum(AttendanceSource), nullable=False, default=AttendanceSource.system)
    change_count = Column(Integer, nullable=False, default=0)
    last_changed_at = Column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint("training_id", "athlete_id", name="uq_attendance_training_athlete"),
        Index("ix_attendance_training_id", "training_id"),
        Index("ix_attendance_athlete_id", "athlete_id"),
    )

    training = relationship(
        "Allenamento",
        backref=backref("attendances", cascade="all,delete-orphan"),
    )
    athlete = relationship("User")


class AttendanceChangeLog(Base):
    __tablename__ = "attendance_change_logs"

    id = Column(Integer, primary_key=True)
    attendance_id = Column(Integer, ForeignKey("attendances.id", ondelete="CASCADE"), nullable=False)
    changed_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    old_status = Column(Enum(AttendanceStatus), nullable=True)
    new_status = Column(Enum(AttendanceStatus), nullable=False)
    source = Column(Enum(AttendanceSource), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    reason = Column(String, nullable=True)

    attendance = relationship(
        "Attendance", backref=backref("changes", cascade="all,delete-orphan")
    )
    changed_by_user = relationship("User")


class AthleteMeasurement(Base):
    __tablename__ = "athlete_measurements"

    id = Column(Integer, primary_key=True)
    athlete_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    measured_at = Column(Date, nullable=False, default=date.today)
    # GENERALI
    height_cm = Column(Float, nullable=True)
    weight_kg = Column(Float, nullable=True)
    # SPECIFICHE
    leg_length_cm = Column(Float, nullable=True)
    tibia_length_cm = Column(Float, nullable=True)
    arm_length_cm = Column(Float, nullable=True)
    torso_height_cm = Column(Float, nullable=True)
    wingspan_cm = Column(Float, nullable=True)
    # NOTE
    notes = Column(Text, nullable=True)

    recorded_by_user_id = Column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    recorded_by = relationship("User", foreign_keys=[recorded_by_user_id])
    athlete = relationship(
        "User",
        foreign_keys=[athlete_id],
        backref=backref("measurements", cascade="all,delete-orphan"),
    )

