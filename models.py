# File: models.py
# Definisce la struttura di tutte le tabelle del database con SQLAlchemy.

from datetime import date
from sqlalchemy import (
    Column, Integer, String, Date, Table, ForeignKey, Float
)
from sqlalchemy.orm import relationship, column_property
from sqlalchemy.sql import func
from database import Base

# --- TABELLE DI ASSOCIAZIONE (MOLTI-A-MOLTI) ---

allenamento_subgroup_association = Table(
    'allenamento_subgroup_association', Base.metadata,
    Column('allenamento_id', Integer, ForeignKey('allenamenti.id'), primary_key=True),
    Column('subgroup_id', Integer, ForeignKey('subgroups.id'), primary_key=True)
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


# --- MODELLI DELLE TABELLE PRINCIPALI ---

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

    # Relazioni
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    tags = relationship("Tag", secondary=user_tags, back_populates="users")
    barche_assegnate = relationship("Barca", secondary=barca_atleti_association, back_populates="atleti_assegnati")
    schede_pesi = relationship("SchedaPesi", back_populates="atleta")
    turni = relationship("Turno", back_populates="user")

    @property
    def age(self) -> int:
        """Calcola l'età attuale in anni compiuti."""
        if not self.date_of_birth:
            return 0
        today = date.today()
        return today.year - self.date_of_birth.year - (
                    (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))

    @property
    def solar_age(self) -> int:
        """Calcola l'età che l'atleta avrà alla fine dell'anno solare corrente."""
        if not self.date_of_birth:
            return 0
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
    def category(self) -> str:
        if self.manual_category:
            return self.manual_category
        if self.is_atleta and self.date_of_birth:
            age = self.solar_age
            if age <= 10: return "Allievo A"
            if age == 11: return "Allievo B1"
            if age == 12: return "Allievo B2"
            if age == 13: return "Allievo C"
            if age == 14: return "Cadetto"
            if 15 <= age <= 16: return "Ragazzo"
            if 17 <= age <= 18: return "Junior"
            if 19 <= age <= 23: return "Under 23"
            if 24 <= age <= 27: return "Senior"
            if age > 27: return "Master"
        return "N/D"

    @property
    def macro_group_name(self) -> str:
        if not self.is_atleta:
            return "N/D"
        cat = self.category
        if cat in ["Allievo A", "Allievo B1", "Allievo B2", "Allievo C", "Cadetto"]:
            return "Under 14"
        elif cat == "Master":
            return "Master"
        elif cat in ["Ragazzo", "Junior", "Under 23", "Senior"]:
            return "Over 14"
        return "N/D"


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
    costruttore = Column(String)
    anno = Column(Integer)
    remi_assegnati = Column(String)
    altezza_scalmi = Column(Float)
    altezza_carrello = Column(Float)
    apertura_totale = Column(Float)
    semiapertura_sx = Column(Float)
    atleti_assegnati = relationship("User", secondary=barca_atleti_association, back_populates="barche_assegnate")


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


class MacroGroup(Base):
    __tablename__ = "macro_groups"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    subgroups = relationship("SubGroup", back_populates="macro_group")


class SubGroup(Base):
    __tablename__ = "subgroups"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    macro_group_id = Column(Integer, ForeignKey('macro_groups.id'))
    macro_group = relationship("MacroGroup", back_populates="subgroups")
    allenamenti = relationship("Allenamento", secondary=allenamento_subgroup_association, back_populates="sub_groups")


class Allenamento(Base):
    __tablename__ = "allenamenti"
    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String, nullable=False)
    descrizione = Column(String)
    data = Column(Date, nullable=False)
    orario = Column(String)
    recurrence_id = Column(String, index=True, nullable=True)
    macro_group_id = Column(Integer, ForeignKey('macro_groups.id'))
    macro_group = relationship("MacroGroup")
    sub_groups = relationship("SubGroup", secondary=allenamento_subgroup_association, back_populates="allenamenti")


class Turno(Base):
    __tablename__ = "turni"
    id = Column(Integer, primary_key=True, index=True)
    data = Column(Date, nullable=False, index=True)
    fascia_oraria = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    user = relationship("User", back_populates="turni")
