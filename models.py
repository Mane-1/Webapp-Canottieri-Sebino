# File: models.py
# Questo file definisce la struttura di tutte le tabelle del database
# usando i modelli di SQLAlchemy.

import uuid
from sqlalchemy import Column, Integer, String, Date, ForeignKey, Table, Float
from sqlalchemy.orm import relationship
from database import Base  # Importiamo la Base creata in database.py

# Tabella di associazione per la relazione Molti-a-Molti
# tra Allenamenti e Sottogruppi.
allenamento_subgroup_association = Table('allenamento_subgroup_association', Base.metadata,
                                         Column('allenamento_id', Integer, ForeignKey('allenamenti.id'),
                                                primary_key=True),
                                         Column('subgroup_id', Integer, ForeignKey('subgroups.id'), primary_key=True)
                                         )

# Tabella di associazione per la relazione Molti-a-Molti
# tra Utenti e Ruoli.
user_roles = Table('user_roles', Base.metadata,
                   Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
                   Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True)
                   )

# Tabella di associazione per la relazione Molti-a-Molti
# tra Barche e Atleti (Utenti).
barca_atleti_association = Table('barca_atleti_association', Base.metadata,
                                 Column('barca_id', Integer, ForeignKey('barche.id'), primary_key=True),
                                 Column('user_id', Integer, ForeignKey('users.id'), primary_key=True)
                                 )


class Role(Base):
    __tablename__ = 'roles'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, index=True)
    phone_number = Column(String)
    date_of_birth = Column(Date, nullable=False)
    enrollment_year = Column(Integer, nullable=False)

    roles = relationship("Role", secondary=user_roles)
    turni = relationship("Turno", back_populates="user")
    barche_assegnate = relationship("Barca", secondary=barca_atleti_association, back_populates="atleti_assegnati")
    schede_pesi = relationship("SchedaPesi", back_populates="atleta")

    @property
    def is_admin(self):
        return any(role.name == 'admin' for role in self.roles)

    @property
    def is_allenatore(self):
        return any(role.name == 'allenatore' for role in self.roles)

    @property
    def is_atleta(self):
        return any(role.name == 'atleta' for role in self.roles)


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

    # CORRETTO: La relazione ora punta a "SubGroup"
    sub_groups = relationship("SubGroup", secondary=allenamento_subgroup_association, back_populates="allenamenti")


class Turno(Base):
    __tablename__ = "turni"
    id = Column(Integer, primary_key=True, index=True)
    data = Column(Date, nullable=False, index=True)
    fascia_oraria = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    user = relationship("User", back_populates="turni")
