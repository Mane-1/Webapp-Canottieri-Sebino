# Directory del Progetto: /Users/gabrielemanenti/PycharmProjects/Webapp_Canottieri_2

---

## File: `models.py`

```python
# File: models.py
# Definisce la struttura di tutte le tabelle del database con SQLAlchemy.

from datetime import date
from sqlalchemy import (
    Column, Integer, String, Date, Table, ForeignKey, Float
)
from sqlalchemy.orm import relationship, object_session
from sqlalchemy.orm.attributes import flag_modified
from database import Base
from functools import lru_cache

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

class Categoria(Base):
    __tablename__ = "categorie"
    id = Column(Integer, primary_key=True)
    nome = Column(String, unique=True, nullable=False)
    eta_min = Column(Integer, nullable=False)
    eta_max = Column(Integer, nullable=False)
    ordine = Column(Integer, default=0)  # Per ordinamento personalizzato se necessario
    macro_group = Column(String, default="N/D")


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
        if not self.date_of_birth:
            return 0
        today = date.today()
        return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))

    @property
    def solar_age(self) -> int:
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
    @lru_cache(maxsize=1)
    def _category_obj(self) -> Categoria | None:
        """
        Metodo interno e "cachato" per recuperare l'oggetto Categoria dal DB.
        Usa object_session per accedere alla sessione del database a cui questo utente è collegato.
        """
        if not self.is_atleta or not self.date_of_birth:
            return None

        db_session = object_session(self)
        if not db_session:
            # Se l'oggetto non è in una sessione, non possiamo fare la query.
            # Questo può accadere in contesti non-http (es. script).
            return None

        age = self.solar_age
        return db_session.query(Categoria).filter(
            Categoria.eta_min <= age,
            Categoria.eta_max >= age
        ).first()

    @property
    def category(self) -> str:
        if self.manual_category:
            return self.manual_category

        categoria_obj = self._category_obj
        return categoria_obj.nome if categoria_obj else "N/D"

    @property
    def macro_group_name(self) -> str:
        if not self.is_atleta:
            return "N/D"

        categoria_obj = self._category_obj
        return categoria_obj.macro_group if categoria_obj else "N/D"


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
```

## File: `database.py`

```python
# File: database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Cerca l'URL del database in una variabile d'ambiente.
# Se non la trova, usa il file SQLite locale per i test.
SQLALCHEMY_DATABASE_URL = os.environ.get(
    "DATABASE_URL", "sqlite:///./canottierisebino.db"
)

# Se l'URL è di PostgreSQL (come su Render), sostituisce il prefisso
# per renderlo compatibile con SQLAlchemy.
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace(
        "postgres://", "postgresql://"
    )

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    # L'argomento `connect_args` è necessario solo per SQLite
    connect_args={"check_same_thread": False} if "sqlite" in SQLALCHEMY_DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

```

## File: `security.py`

```python
# File: security.py
# Questo file contiene tutte le funzioni e le configurazioni
# relative alla sicurezza, come la gestione delle password.

from passlib.context import CryptContext

# 1. Configurazione del contesto per l'hashing delle password
# Usiamo bcrypt come algoritmo di hashing, che è lo standard di sicurezza attuale.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# 2. Funzioni di verifica e hashing

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica se una password in chiaro corrisponde a una password hashata.

    Args:
        plain_password: La password inserita dall'utente.
        hashed_password: La password salvata nel database.

    Returns:
        True se le password corrispondono, altrimenti False.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Genera l'hash di una password.

    Args:
        password: La password in chiaro da hashare.

    Returns:
        La stringa della password hashata.
    """
    return pwd_context.hash(password)

```

## File: `export_code.py`

```python
import os


def export_project_to_file(project_path, output_file_path):
    """
    Esporta i file .py di un progetto in un singolo file markdown,
    includendo la directory del progetto in cima.
    """
    # Converte il percorso in un percorso assoluto per chiarezza
    abs_project_path = os.path.abspath(project_path)

    with open(output_file_path, 'w', encoding='utf-8') as outfile:
        # --- MODIFICA RICHIESTA ---
        # Scrive la directory principale del progetto all'inizio del file.
        outfile.write(f"# Directory del Progetto: {abs_project_path}\n\n")
        outfile.write("---\n\n")  # Aggiunge un separatore per chiarezza

        for root, dirs, files in os.walk(abs_project_path):
            # Ignora le cartelle comuni che non contengono codice utile
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'venv', '.idea']]

            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, abs_project_path)

                    # Usa un titolo di livello 2 per ogni file
                    outfile.write(f"## File: `{relative_path}`\n\n")

                    # Miglioramento: usa blocchi di codice Markdown per il syntax highlighting
                    outfile.write("```python\n")
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as infile:
                            outfile.write(infile.read())
                    except Exception as e:
                        outfile.write(f"# Errore nella lettura del file: {e}")
                    outfile.write("\n```\n\n")


# --- Configurazione ---
# Sostituisci con il percorso del tuo progetto.
# Puoi anche usare '.' se questo script si trova nella cartella principale del progetto.
project_dir = '/Users/gabrielemanenti/PycharmProjects/Webapp_Canottieri_2'
output_file = 'codice_progetto.md'

if __name__ == "__main__":
    export_project_to_file(project_dir, output_file)
    print(f"✅ Codice del progetto esportato con successo in '{output_file}'")
```

## File: `seed.py`

```python
# File: seed.py
# Script per popolare il database con tutti i dati iniziali.

import os
import sys
from datetime import date, datetime
import logging

# Aggiunge la directory principale al path per le importazioni
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
import models
import security

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- DATI ESTRATTI E PULITI DAL PDF ---
atleti_data = [
    # ... i tuoi dati degli atleti rimangono invariati ...
    {'nome': 'MASSIMO', 'cognome': 'ARMENI', 'data_nascita': '01/10/1968', 'email': 'massimoarmeni@icloud.com',
     'cf': 'RMNMSM68R01L117G', 'data_tess': '08/01/2025', 'scad_cert': '04/11/2025',
     'indirizzo': 'VIA OTTORINO VILLA 18 - 25124 BRESCIA'},
    {'nome': 'GIADA', 'cognome': 'BELLI', 'data_nascita': '21/08/2012', 'email': 'sonia.moretti@virgilio.it',
     'cf': 'BLLGDI12M61B157H', 'data_tess': '08/01/2025', 'scad_cert': '17/01/2026',
     'indirizzo': 'VIA NAZIONALE, 55 - 24060 PIANICO'},
    {'nome': 'MATTIA', 'cognome': 'BELLI', 'data_nascita': '21/08/2012', 'email': 'sonia.moretti@virgilio.it',
     'cf': 'BLLMTT12M21B157B', 'data_tess': '08/01/2025', 'scad_cert': '17/01/2026',
     'indirizzo': 'VIA NAZIONALE, 55 - 24060 PIANICO'},
    {'nome': 'PIETRO', 'cognome': 'BIANCHI', 'data_nascita': '06/01/2009', 'email': 'giusy.foresti@virgilio.it',
     'cf': 'BNCPTR09A06D434K', 'data_tess': '08/01/2025', 'scad_cert': '26/09/2025',
     'indirizzo': 'VIA DEI FANTONI, 5 - 24060 SOLTO COLLINA'},
    {'nome': 'TOMMASO', 'cognome': 'BIGONI', 'data_nascita': '23/01/2007', 'email': 'tommasobigoni@outlook.it',
     'cf': 'BGNTMS07A23A794E', 'data_tess': '08/01/2025', 'scad_cert': '03/06/2026',
     'indirizzo': 'VIA ANTONIO LOCATELLI, 9 - 24060 ENDINE GAIANO'},
    {'nome': 'ALESSANDRO', 'cognome': 'BONETTI', 'data_nascita': '12/02/2013', 'email': 'claudia.delasa@tiscali.it',
     'cf': 'BNTLSN13B12D434S', 'data_tess': '08/01/2025', 'scad_cert': '23/04/2026',
     'indirizzo': 'VIA MAMELI NR 7 - 24060 ROGNO'},
    {'nome': 'REBECCA', 'cognome': 'BONETTI', 'data_nascita': '24/07/2010', 'email': 'claudia.delasa@tiscali.it',
     'cf': 'BNTRCC10L64D434Q', 'data_tess': '08/01/2025', 'scad_cert': '22/08/2025',
     'indirizzo': 'VIA GOFFREDO MAMELI, 7 - 24060 ROGNO'},
    {'nome': 'ARISTIDE', 'cognome': 'BONOMELLI', 'data_nascita': '25/09/1982', 'email': 'aristidebonomelli@hotmail.com',
     'cf': 'BNMRTD82P251628S', 'data_tess': '24/03/2025', 'scad_cert': '10/03/2026',
     'indirizzo': 'VIA TONALE E MENDOLA 198 - 24060 ENDINE GAIANO'},
    {'nome': 'ANASTASIA', 'cognome': 'BUZZI', 'data_nascita': '29/06/2011', 'email': 'f.bettineschi@hotmail.it',
     'cf': 'BZZNTS11H69A794R', 'data_tess': '08/01/2025', 'scad_cert': '26/02/2025',
     'indirizzo': 'VIA DON G PEZZOTTA, 322 - 24060 RANZANICO'},
    {'nome': 'SOFIA', 'cognome': 'CABRINI', 'data_nascita': '12/03/2010', 'email': 'sofiacabrini2010@gmail.com',
     'cf': 'CBRSFO10C52G574F', 'data_tess': '20/03/2025', 'scad_cert': '25/02/2026',
     'indirizzo': 'VIA SAN DEFENDENTE NR 48 - 24023 CLUSONE'},
    {'nome': 'MARCO', 'cognome': 'CAMBIERI', 'data_nascita': '03/02/2002', 'email': 'marcocambieri2002@gmail.com',
     'cf': 'CMBMRC02B03C800T', 'data_tess': '05/06/2025', 'scad_cert': '29/05/2026',
     'indirizzo': 'VIA G. PAGLIA 6 - 24065 LOVERE'},
    {'nome': 'PAOLO', 'cognome': 'CANU', 'data_nascita': '08/10/1961', 'email': 'paolo.canu@unipd.it',
     'cf': 'CNAPLA61R08E704H', 'data_tess': '08/01/2025', 'scad_cert': '02/10/2025',
     'indirizzo': 'VIA COLLE NR 3 - 24069 TRESCORE BALNEARIO'},
    {'nome': 'AMELIA', 'cognome': 'CENSI', 'data_nascita': '27/07/2010', 'email': 'info@canottierisebino.it',
     'cf': 'CNSMLA10L67E3330', 'data_tess': '08/01/2025', 'scad_cert': '14/01/2026',
     'indirizzo': 'VIA CASINO BAGLIONI, 17 - 24062 COSTA VOLPINO'},
    {'nome': 'CHLOE ANGELICA', 'cognome': 'CHAUVET', 'data_nascita': '08/09/2010',
     'email': 'emilianegrinotti@gmail.com', 'cf': 'CHVCLN10P48G752W', 'data_tess': '08/01/2025',
     'scad_cert': '23/11/2025', 'indirizzo': 'VIA RONCHELLI NR.10 - 24060 RIVA DI SOLTO'},
    {'nome': 'BENEDETTO', 'cognome': 'CHIARELLI', 'data_nascita': '24/03/2009', 'email': 'benedetto09@gmail.com',
     'cf': 'CHRBDT09C24G574E', 'data_tess': '08/01/2025', 'scad_cert': '24/04/2026',
     'indirizzo': 'VIA GIARDINI, 9 - 24060 BOSSICO'},
    {'nome': 'CARLOS', 'cognome': 'COCCHETTI', 'data_nascita': '14/05/2014', 'email': 'maddalena-baiguini@tiscali.it',
     'cf': 'CCCCLS14E14D434F', 'data_tess': '14/01/2025', 'scad_cert': '11/01/2026',
     'indirizzo': 'VIA BREDE, 3 - 24062 COSTA VOLPINO'},
    {'nome': 'ANDREA', 'cognome': 'COLOMBI', 'data_nascita': '03/10/2013', 'email': 'semper.b@email.it',
     'cf': 'CLMNDR13R0381571', 'data_tess': '08/01/2025', 'scad_cert': '20/01/2026',
     'indirizzo': 'VIA XXV APRILE NR 8/A - 24063 CASTRO'},
    {'nome': 'GIOELE', 'cognome': 'COTTI COMETTINI', 'data_nascita': '01/02/2013', 'email': 'manuela.uberti@gmail.com',
     'cf': 'CTTGLI13B01A794Q', 'data_tess': '08/01/2025', 'scad_cert': '27/01/2026',
     'indirizzo': 'VIA ORTIGARA 8/D - 24062 COSTA VOLPINO'},
    {'nome': 'STEFANO', 'cognome': 'DELBELLO', 'data_nascita': '14/06/1986', 'email': 'stefanodelbello@gmail.com',
     'cf': 'DLBSFN86H14E7040', 'data_tess': '08/01/2025', 'scad_cert': '13/02/2026',
     'indirizzo': "VIA F.LLI CALVI, 9 - 24060 SOVERE"},
    {'nome': 'ANDREA', 'cognome': 'FACCHINETTI', 'data_nascita': '11/08/2011', 'email': 'gloria.franzoni.gf@gmail.com',
     'cf': 'FCCNDR11M11E333U', 'data_tess': '08/01/2025', 'scad_cert': '08/12/2025',
     'indirizzo': 'VIA PINETA 14 - 25050 OSSIMO'},
    {'nome': 'NICOLA', 'cognome': 'FIGAROLI', 'data_nascita': '11/05/2010', 'email': 'elena.76@gmail.com',
     'cf': 'FGRNCL10E11G574X', 'data_tess': '08/01/2025', 'scad_cert': '30/01/2026',
     'indirizzo': 'VIA SETTE COLLI, 103/B - 24060 BOSSICO'},
    {'nome': 'ALESSANDRO', 'cognome': 'FRANINI', 'data_nascita': '30/08/2010', 'email': 'fari.simo@alice.it',
     'cf': 'FRNLSN10M30D434C', 'data_tess': '08/01/2025', 'scad_cert': '12/12/2025',
     'indirizzo': 'VIA AURORA.NR 6 - 24062 COSTA VOLPINO'},
    {'nome': 'ANNA', 'cognome': 'FRANINI', 'data_nascita': '02/01/2013', 'email': 'fari.simo@alice.it',
     'cf': 'FRNNNA13A42D434Q', 'data_tess': '08/01/2025', 'scad_cert': '25/01/2026',
     'indirizzo': 'VIA AURORA NR 6 - 24062 COSTA VOLPINO'},
    {'nome': 'MICHELE', 'cognome': 'GALLIZIOLI', 'data_nascita': '19/08/2011', 'email': 'helenatorri42@gmail.com',
     'cf': 'GLLMHL11M19D434F', 'data_tess': '08/01/2025', 'scad_cert': '14/01/2026',
     'indirizzo': 'VIA GIUSEPPE GARIBALDI NR 22 24063-CASTRO'},
    {'nome': 'PAOLO', 'cognome': 'GHIDINI', 'data_nascita': '06/08/1992', 'email': 'paologhidini92@gmail.com',
     'cf': 'GHDPLA92M06E704E', 'data_tess': '08/01/2025', 'scad_cert': '13/03/2026',
     'indirizzo': 'VIA IV NOVEMBRE NR 22 - 24065 LOVERE'},
    {'nome': 'GIORGIA', 'cognome': 'GIRELLI', 'data_nascita': '30/05/1997', 'email': 'giorgiagirelliscuola@gmail.com',
     'cf': 'GRLGRG97E70D434V', 'data_tess': '08/01/2025', 'scad_cert': '03/03/2026',
     'indirizzo': 'VIA CAMILLO CAVOUR, 16A - 25047 DARFO BOARIO TERME'},
    {'nome': 'SIMONA', 'cognome': 'GUARNERI', 'data_nascita': '18/09/1971', 'email': 'guameri_simona@libero.it',
     'cf': 'GRNSMN71P58F119R', 'data_tess': '08/01/2025', 'scad_cert': '20/09/2025',
     'indirizzo': 'VIA PALAZZINE, 27 - 24060 FONTENO'},
    {'nome': 'EMMA', 'cognome': 'GUERINI', 'data_nascita': '06/10/2011', 'email': 'stefini.sara@gmail.com',
     'cf': 'GRNIMME11R46D4341', 'data_tess': '08/01/2025', 'scad_cert': '23/05/2026',
     'indirizzo': "VIA CA' POETA, 9 - 24062 COSTA VOLPINO"},
    {'nome': 'GABRIELE', 'cognome': 'GUERINI', 'data_nascita': '22/04/2010', 'email': 'stefini.sara@gmail.com',
     'cf': 'GRNGRL10D22D434L', 'data_tess': '08/01/2025', 'scad_cert': '10/03/2026',
     'indirizzo': "VIA CA' POETA NR 9 - 24062 COSTA VOLPINO"},
    {'nome': 'ALICE', 'cognome': 'IANNONE', 'data_nascita': '29/03/2013', 'email': 'nikianno@alice.it',
     'cf': 'NNNLCA13C69E333V', 'data_tess': '08/01/2025', 'scad_cert': '26/03/2026',
     'indirizzo': 'VIA PAPA GIOVANNI PAOLO 1, 29 - 24060 SOVERE'},
    {'nome': 'ANTONIO', 'cognome': 'IANNONE', 'data_nascita': '06/01/2011', 'email': 'nikianno@alice.it',
     'cf': 'NNNNTN11A06E333B', 'data_tess': '08/01/2025', 'scad_cert': '21/03/2025',
     'indirizzo': 'VIA PAPA GIOVANNI PAOLO 1, 29 - 24060 SOVERE'},
    {'nome': 'SANDRA', 'cognome': 'LEONARDI', 'data_nascita': '13/07/1975', 'email': 'a_leosan@hotmail.com',
     'cf': 'LNRSDR75L53A290Q', 'data_tess': '08/01/2025', 'scad_cert': '25/03/2026',
     'indirizzo': 'VIALE ALCIDE DE GASPERI, 36 - 25047 DARFO BOARIO TERME'},
    {'nome': 'NICOLA', 'cognome': 'MANELLA', 'data_nascita': '22/06/1990', 'email': 'nicola.manella@yahoo.it',
     'cf': 'MNLNCL90H22E704J', 'data_tess': '08/01/2025', 'scad_cert': '03/03/2026',
     'indirizzo': 'VIA TORRICELLA 25/D - 24065 LOVERE'},
    {'nome': 'GIANBATTISTA', 'cognome': 'MARTINOLI', 'data_nascita': '29/09/1963', 'email': 'martigianni@gmail.com',
     'cf': 'MRTGBT63P29E704S', 'data_tess': '08/01/2025', 'scad_cert': '03/10/2025',
     'indirizzo': 'VIA DEL SERRO, 12 - 24063 CASTRO'},
    {'nome': 'ELISA', 'cognome': 'MARZELLA', 'data_nascita': '10/04/2007', 'email': 'lella.catta@gmail.com',
     'cf': 'MRZLSE07D50C800Y', 'data_tess': '08/01/2025', 'scad_cert': '11/01/2026',
     'indirizzo': 'VIA CAMILLO CAVOUR, 71 - 24028 PONTE NOSSA'},
    {'nome': 'LUCIA', 'cognome': 'MAZZA', 'data_nascita': '25/05/2010', 'email': 'casalemazza@gmail.com',
     'cf': 'MZZLCU10E65G574J', 'data_tess': '08/01/2025', 'scad_cert': '23/09/2025',
     'indirizzo': 'VIA GAIA, 34 - 24065 LOVERE'},
    {'nome': 'ANNA', 'cognome': 'OSCAR', 'data_nascita': '18/06/1959', 'email': 'anussi@alice.it',
     'cf': 'SCRNNA59H58A794X', 'data_tess': '08/01/2025', 'scad_cert': '02/10/2025',
     'indirizzo': 'VIA COLLE NR 3 - 24069 TRESCORE BALNEARIO'},
    {'nome': 'BEATRICE', 'cognome': 'PEDRAZZANI', 'data_nascita': '14/01/2012',
     'email': 'matteo.pedrazzani75@gmail.com', 'cf': 'PDRBRC12A54A470H', 'data_tess': '08/01/2025',
     'scad_cert': '09/11/2025', 'indirizzo': 'VIA SAN GOTTARDO NR 9 - 24062 COSTA VOLPINO'},
    {'nome': 'ANNA', 'cognome': 'PERINI', 'data_nascita': '17/07/1968', 'email': 'anna.perini@icteam.it',
     'cf': 'PRNNNA68L57A794B', 'data_tess': '08/01/2025', 'scad_cert': '16/04/2026',
     'indirizzo': 'PIAZZA MADRE TERESA DI CALCUTTA 9 - 24020 VILLA DI SERIO'},
    {'nome': 'ALESSANDRA', 'cognome': 'PICINELLI', 'data_nascita': '25/10/1976',
     'email': 'picinelli.alessandra@gmail.com', 'cf': 'PCNLSN76R65E704L', 'data_tess': '08/01/2025',
     'scad_cert': '10/07/2025', 'indirizzo': 'VIA DELLA BOSCHETTA, 11 - 24062 COSTA VOLPINO'},
    {'nome': 'SERGIO', 'cognome': 'QUARENGHI', 'data_nascita': '29/11/1968', 'email': 'sergio.quarenghi@libero.it',
     'cf': 'QRNSRG68S29B157A', 'data_tess': '08/01/2025', 'scad_cert': '11/03/2026',
     'indirizzo': 'VIA VIGHENZI NR 3 - 25124 BRESCIA'},
    {'nome': 'CHIARA', 'cognome': 'RONCHETTI', 'data_nascita': '16/11/2011', 'email': 'mauroronchetti@hotmail.it',
     'cf': 'RNCCHR11S56G574A', 'data_tess': '08/01/2025', 'scad_cert': '04/03/2026',
     'indirizzo': 'VIA CAPOFERRI, 1 - 24063 CASTRO'},
    {'nome': 'GIULIA', 'cognome': 'ROTA', 'data_nascita': '29/05/2008', 'email': 'andrearotaedania@gmail.com',
     'cf': 'RTOGLI08E69D434V', 'data_tess': '08/01/2025', 'scad_cert': '08/10/2025',
     'indirizzo': 'VIA NAZIONALE NR 7 - 24062 COSTA VOLPINO'},
    {'nome': 'CHIARA', 'cognome': 'RUSCITTO', 'data_nascita': '29/01/1973', 'email': 'chiara.ruscitto@gmail.com',
     'cf': 'RSCCHR73T69L388R', 'data_tess': '07/04/2025', 'scad_cert': '01/10/2025',
     'indirizzo': 'VIA TERZAGO 3 - 24020 SCANZOROSCIATE'},
    {'nome': 'DANIELE', 'cognome': 'SBARDOLINI', 'data_nascita': '28/04/1989', 'email': 'danielesbardolini@tiscali.it',
     'cf': 'SBRDNL89D28B149H', 'data_tess': '07/04/2025', 'scad_cert': '28/03/2026',
     'indirizzo': 'VIA CASTELLAZZO NR 30 - 25055 PISOGNE'},
    {'nome': 'MATTIA', 'cognome': 'SERRA', 'data_nascita': '14/07/2010', 'email': 'smatti1410@gmail.com',
     'cf': 'SRRMTT10L14H501M', 'data_tess': '24/02/2025', 'scad_cert': '30/01/2026',
     'indirizzo': 'VIALE DANTE ALIGHIERI, 5 - 24065 LOVERE'},
    {'nome': 'GIOVANNI', 'cognome': 'SILVESTRI', 'data_nascita': '24/11/2010', 'email': 'luigisilvestri@live.com',
     'cf': 'SLVGNN10S24D434P', 'data_tess': '08/01/2025', 'scad_cert': '28/01/2026',
     'indirizzo': 'VIA FRATELLI CALVI NR 8 - 24060 PIANICO'},
    {'nome': 'EMMA', 'cognome': 'STERNI', 'data_nascita': '26/11/2008', 'email': 'emmastemi08@gmail.com',
     'cf': 'STRMME08S66I628D', 'data_tess': '08/01/2025', 'scad_cert': '10/12/2025',
     'indirizzo': 'VIA CESARE BATTISTI NR 1 - 24060 ROGNO'},
    {'nome': 'PAOLO ALBERTO', 'cognome': 'STERNI', 'data_nascita': '28/04/1979', 'email': 'paolosterni@gmail.com',
     'cf': 'STRPLB79D28I628B', 'data_tess': '19/02/2025', 'scad_cert': '27/12/2025',
     'indirizzo': 'VIA ARIA LIBERA, 12 - 24062 COSTA VOLPINO'},
    {'nome': 'LORENZO', 'cognome': 'TURLA', 'data_nascita': '09/03/2009', 'email': 'barby.foresti@gmail.com',
     'cf': 'TRLLNZ09C09E333S', 'data_tess': '08/01/2025', 'scad_cert': '23/01/2026',
     'indirizzo': 'VIA CURO, 8 - 24062 COSTA VOLPINO'},
    {'nome': 'ALESSANDRO', 'cognome': 'ZAMBETTI', 'data_nascita': '13/03/2015', 'email': 'mauramoviggia@hotmail.com',
     'cf': 'ZMBLSN15C13B157I', 'data_tess': '28/04/2025', 'scad_cert': '14/11/2025',
     'indirizzo': 'VIA MADRERA NR 52 - 24060 RANZANICO'},
    {'nome': 'LEONARDO', 'cognome': 'ZANA', 'data_nascita': '23/12/2010', 'email': 'n.zana@lucchinirs.com',
     'cf': 'ZNALRD10T23D434C', 'data_tess': '08/01/2025', 'scad_cert': '10/04/2026',
     'indirizzo': 'VIA QUAIA NR 5 - 24060 PIANICO'},
    {'nome': 'NOEMI', 'cognome': 'ZANA', 'data_nascita': '03/09/2012', 'email': 'n.zana@lucchinirs.com',
     'cf': 'ZNANMO12P43D434S', 'data_tess': '09/01/2025', 'scad_cert': '05/11/2025',
     'indirizzo': 'VIA QUAIA NR 5 - 24060 PIANICO'},
]


def seed_categories(db: Session):
    """Popola la tabella delle categorie con i dati standard."""
    logger.info("Popolamento categorie...")
    if db.query(models.Categoria).count() > 0:
        logger.info("Tabella categorie già popolata. Skippo.")
        return

    categorie = [
        # Dati basati sulle regole federali
        models.Categoria(nome="Allievo A", eta_min=0, eta_max=10, ordine=1, macro_group="Under 14"),
        models.Categoria(nome="Allievo B1", eta_min=11, eta_max=11, ordine=2, macro_group="Under 14"),
        models.Categoria(nome="Allievo B2", eta_min=12, eta_max=12, ordine=3, macro_group="Under 14"),
        models.Categoria(nome="Allievo C", eta_min=13, eta_max=13, ordine=4, macro_group="Under 14"),
        models.Categoria(nome="Cadetto", eta_min=14, eta_max=14, ordine=5, macro_group="Under 14"),
        models.Categoria(nome="Ragazzo", eta_min=15, eta_max=16, ordine=6, macro_group="Over 14"),
        models.Categoria(nome="Junior", eta_min=17, eta_max=18, ordine=7, macro_group="Over 14"),
        models.Categoria(nome="Under 23", eta_min=19, eta_max=23, ordine=8, macro_group="Over 14"),
        models.Categoria(nome="Senior", eta_min=24, eta_max=27, ordine=9, macro_group="Over 14"),
        models.Categoria(nome="Master", eta_min=28, eta_max=150, ordine=10, macro_group="Master"),
    ]
    db.add_all(categorie)
    db.commit()
    logger.info("Categorie popolate con successo.")


def main():
    """Funzione principale per eseguire il seeding del database."""
    logger.info("Avvio script di seeding completo...")

    logger.info("ATTENZIONE: Verranno cancellati tutti i dati esistenti nel database.")
    input("Premi Invio per continuare, o CTRL+C per annullare...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    logger.info("Tabelle create.")

    db = SessionLocal()
    try:
        # 1. Popola Ruoli
        logger.info("Popolamento dei ruoli...")
        ruoli_da_creare = ['atleta', 'allenatore', 'admin']
        for nome_ruolo in ruoli_da_creare:
            if not db.query(models.Role).filter_by(name=nome_ruolo).first():
                db.add(models.Role(name=nome_ruolo))
        db.commit()

        # NUOVO: Popola Categorie
        seed_categories(db)

        # 2. Crea Utente Admin
        logger.info("Creazione utente admin...")
        if not db.query(models.User).filter(models.User.username == "gabriele").first():
            admin_role = db.query(models.Role).filter_by(name='admin').one()
            allenatore_role = db.query(models.Role).filter_by(name='allenatore').one()
            admin_user = models.User(
                username="gabriele",
                hashed_password=security.get_password_hash("manenti"),
                first_name="Gabriele",
                last_name="Manenti",
                email="gabriele.manenti@example.com",
                phone_number="3331234567",
                date_of_birth=date(1990, 1, 1),
                enrollment_year=2020,
                roles=[admin_role, allenatore_role]
            )
            db.add(admin_user)
            db.commit()
            logger.info("Utente admin 'gabriele' creato.")

        # 3. Popola Atleti
        logger.info("Inizio creazione atleti...")
        atleta_role = db.query(models.Role).filter_by(name='atleta').one()
        emails_usate = set()

        # Aggiungiamo l'email dell'admin per evitare conflitti
        admin_email = "gabriele.manenti@example.com"
        if db.query(models.User).filter(models.User.email == admin_email).first():
            emails_usate.add(admin_email)

        for atleta in atleti_data:
            nome = atleta['nome'].title()
            cognome = atleta['cognome'].title()
            username_base = f"{nome.split(' ')[0]}.{cognome.split(' ')[0]}".lower().replace("'", "")
            username = username_base

            counter = 1
            while db.query(models.User).filter(models.User.username == username).first():
                username = f"{username_base}{counter}"
                counter += 1

            # --- NUOVA GESTIONE EMAIL DUPLICATE ---
            original_email = atleta['email']
            final_email = original_email

            if final_email in emails_usate:
                logger.warning(f"Email duplicata trovata: {original_email} per {nome} {cognome}. Creo una variante.")
                try:
                    local_part, domain = original_email.split('@')
                    email_counter = 1
                    while True:
                        final_email = f"{local_part}+{email_counter}@{domain}"
                        if final_email not in emails_usate:
                            break
                        email_counter += 1
                    logger.info(f"Nuova email generata: {final_email}")
                except ValueError:  # Gestisce email malformate
                    logger.error(f"Formato email non valido: {original_email}. Salto l'utente.")
                    continue

            # Controlla se l'email finale è già nel DB per sicurezza
            if db.query(models.User).filter(models.User.email == final_email).first():
                logger.warning(f"L'email {final_email} è già presente nel DB. Salto l'utente {username}")
                continue

            # --- FINE NUOVA GESTIONE ---

            new_user = models.User(
                username=username,
                hashed_password=security.get_password_hash(username),
                first_name=nome,
                last_name=cognome,
                email=final_email,  # Usa l'email finale (potenzialmente modificata)
                date_of_birth=datetime.strptime(atleta['data_nascita'], '%d/%m/%Y').date(),
                tax_code=atleta.get('cf'),
                membership_date=datetime.strptime(atleta['data_tess'], '%d/%m/%Y').date(),
                certificate_expiration=datetime.strptime(atleta['scad_cert'], '%d/%m/%Y').date(),
                address=atleta.get('indirizzo', '').replace('\n', ' ')
            )
            new_user.roles.append(atleta_role)
            db.add(new_user)
            emails_usate.add(final_email)  # Aggiunge l'email usata al set
            logger.info(f"Creato utente: {username} con email {final_email}")

        db.commit()
        logger.info("Atleti popolati con successo.")

    except Exception as e:
        logger.error(f"Errore durante il seeding: {e}")
        db.rollback()
    finally:
        db.close()

    logger.info("Seeding completato!")


if __name__ == "__main__":
    main()
```

## File: `utils.py`

```python
# File: utils.py
# Descrizione: Contiene funzioni di utilità generiche riutilizzate in diverse parti dell'applicazione.

from datetime import date, datetime, time, timedelta
from typing import Optional, Tuple
from dateutil.rrule import MO, TU, WE, TH, FR, SA, SU

def get_color_for_type(training_type: Optional[str]) -> str:
    """
    Restituisce un codice colore esadecimale basato sul tipo di allenamento.
    """
    colors = {
        "Barca": "#0d6efd",
        "Remoergometro": "#198754",
        "Corsa": "#6f42c1",
        "Pesi": "#dc3545",
        "Circuito": "#fd7e14",
        "Altro": "#212529"
    }
    return colors.get(training_type, "#6c757d")


DAY_MAP_DATETIL = {
    "Lunedì": MO, "Martedì": TU, "Mercoledì": WE, "Giovedì": TH,
    "Venerdì": FR, "Sabato": SA, "Domenica": SU
}


def parse_time_string(time_str: str) -> time:
    """
    Converte una stringa 'HH:MM' in un oggetto time.
    """
    try:
        hour, minute = map(int, time_str.split(':'))
        return time(hour, minute)
    except (ValueError, TypeError):
        return time(0, 0)


def parse_orario(base_date: date, orario_str: str) -> Tuple[datetime, datetime]:
    """
    Converte una stringa di orario (es. "8:00-10:00") in un tuple
    di oggetti datetime di inizio e fine.
    """
    if not orario_str or orario_str.lower() == "personalizzato":
        return datetime.combine(base_date, time.min), datetime.combine(base_date, time.max)
    try:
        if '-' in orario_str:
            start_part, end_part = orario_str.split('-')
            start_time_obj = parse_time_string(start_part.strip())
            end_time_obj = parse_time_string(end_part.strip())
        else:
            start_time_obj = parse_time_string(orario_str.strip())
            end_time_obj = (datetime.combine(base_date, start_time_obj) + timedelta(hours=1)).time()

        start_dt = datetime.combine(base_date, start_time_obj)
        end_dt = datetime.combine(base_date, end_time_obj)
        return start_dt, end_dt
    except Exception:
        return datetime.combine(base_date, time.min), datetime.combine(base_date, time.max)

```

## File: `main.py`

```python
# File: main.py
# Descrizione: File principale dell'applicazione. Inizializza FastAPI, configura middleware,
# template, file statici, eventi di startup e include i router modulari.

import os
import logging
from datetime import date

from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

# Importa i moduli del progetto
import models
import security
from database import engine, Base, SessionLocal
from utils import get_color_for_type
from routers import authentication, users, trainings, resources, admin

# Configurazione del logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Creazione dell'istanza FastAPI
app = FastAPI(title="Gestionale Canottieri")

# Configurazione del middleware per le sessioni
SECRET_KEY = os.environ.get('SECRET_KEY', 'un-segreto-di-default-non-sicuro')
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Configurazione dei template Jinja2 e dei file statici
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates.env.globals['get_color_for_type'] = get_color_for_type


# Evento di startup dell'applicazione
@app.on_event("startup")
def on_startup():
    """
    Esegue operazioni all'avvio dell'applicazione:
    1. Crea le tabelle del database se non esistono.
    2. Popola i dati essenziali (ruoli, utente admin) se il database è vuoto.
    """
    logger.info("Avvio dell'applicazione in corso...")
    Base.metadata.create_all(bind=engine)
    logger.info("Verifica tabelle completata.")

    db = SessionLocal()
    try:
        if db.query(models.Role).count() == 0:
            logger.info("Popolamento dei ruoli...")
            db.add_all([
                models.Role(name='atleta'),
                models.Role(name='allenatore'),
                models.Role(name='admin')
            ])
            db.commit()

        if not db.query(models.User).filter(models.User.username == "gabriele").first():
            logger.info("Creazione utente admin...")
            admin_role = db.query(models.Role).filter_by(name='admin').one()
            allenatore_role = db.query(models.Role).filter_by(name='allenatore').one()
            admin_user = models.User(
                username="gabriele",
                hashed_password=security.get_password_hash("manenti"),
                first_name="Gabriele",
                last_name="Manenti",
                email="gabriele.manenti@example.com",
                date_of_birth=date(1990, 1, 1),
                roles=[admin_role, allenatore_role]
            )
            db.add(admin_user)
            db.commit()
            logger.info("Utente admin 'gabriele' creato.")
    except Exception as e:
        logger.error(f"Errore durante il popolamento dei dati di base all'avvio: {e}")
        db.rollback()
    finally:
        db.close()

# Inclusione dei router modulari
# Ogni router gestisce una sezione specifica dell'applicazione
app.include_router(authentication.router)
app.include_router(users.router)
app.include_router(trainings.router)
app.include_router(resources.router)
app.include_router(admin.router)

```

## File: `dependencies.py`

```python
# File: dependencies.py
# Descrizione: Contiene le dipendenze riutilizzabili per le route FastAPI,
# in particolare per l'autenticazione e l'autorizzazione degli utenti.

from fastapi import Request, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from database import get_db
import models

async def get_current_user(request: Request, db: Session = Depends(get_db)) -> models.User:
    """
    Dipendenza per ottenere l'utente attualmente autenticato dalla sessione.
    Se l'utente non è loggato o non esiste, solleva un'eccezione HTTP
    che causa un redirect alla pagina di login.
    """
    user_id = request.session.get("user_id")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            detail="Non autenticato",
            headers={"Location": "/login"}
        )

    user = db.query(models.User).options(joinedload(models.User.roles)).filter(models.User.id == user_id).first()

    if user is None:
        request.session.pop("user_id", None)
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            detail="Utente non trovato",
            headers={"Location": "/login"}
        )
    return user


async def get_current_admin_user(current_user: models.User = Depends(get_current_user)) -> models.User:
    """
    Dipendenza che verifica se l'utente corrente ha il ruolo di 'admin'.
    Se non è un admin, solleva un'eccezione 403 Forbidden.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accesso negato. Sono richiesti privilegi di amministratore."
        )
    return current_user

```

## File: `routers/users.py`

```python
# File: routers/users.py
# Descrizione: Contiene le route per le pagine principali (root, dashboard),
# la gestione del profilo utente e la rubrica.

from typing import Optional
from datetime import date

from fastapi import APIRouter, Request, Depends, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session, joinedload
from fastapi.templating import Jinja2Templates

import models
import security
from database import get_db
from dependencies import get_current_user

router = APIRouter(tags=["Utenti e Pagine Principali"])
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=RedirectResponse, include_in_schema=False)
async def root(request: Request):
    if request.session.get("user_id"):
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db),
                    current_user: models.User = Depends(get_current_user)):
    today = date.today()
    dashboard_data = {}
    if current_user.is_allenatore:
        dashboard_data['prossimi_turni'] = db.query(models.Turno).filter(models.Turno.user_id == current_user.id,
                                                                         models.Turno.data >= today).order_by(
            models.Turno.data).limit(3).all()
    if current_user.is_atleta:
        subgroups = db.query(models.SubGroup).filter(models.SubGroup.name == current_user.category).all()
        if subgroups:
            subgroup_ids = [sg.id for sg in subgroups]
            dashboard_data['prossimi_allenamenti'] = db.query(models.Allenamento).join(
                models.allenamento_subgroup_association).filter(
                models.allenamento_subgroup_association.c.subgroup_id.in_(subgroup_ids),
                models.Allenamento.data >= today).order_by(models.Allenamento.data).limit(3).all()
    return templates.TemplateResponse("dashboard.html", {"request": request, "current_user": current_user,
                                                         "dashboard_data": dashboard_data})


@router.get("/profilo", response_class=HTMLResponse)
async def view_profile(request: Request, current_user: models.User = Depends(get_current_user)):
    return templates.TemplateResponse("profilo.html",
                                      {"request": request, "user": current_user, "current_user": current_user})


@router.get("/profilo/modifica", response_class=HTMLResponse)
async def edit_profile_form(request: Request, current_user: models.User = Depends(get_current_user)):
    return templates.TemplateResponse("profilo_modifica.html",
                                      {"request": request, "user": current_user, "current_user": current_user})


@router.post("/profilo/modifica", response_class=RedirectResponse)
async def update_profile(
        db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user),
        email: Optional[str] = Form(None), phone_number: Optional[str] = Form(None),
        new_password: Optional[str] = Form(None)
):
    # L'oggetto current_user è legato alla sessione del DB, quindi le modifiche vengono tracciate
    current_user.email = email
    current_user.phone_number = phone_number
    if new_password:
        current_user.hashed_password = security.get_password_hash(new_password)
    db.commit()
    return RedirectResponse(url="/profilo?message=Profilo aggiornato con successo",
                            status_code=303)


@router.get("/rubrica", response_class=HTMLResponse)
async def view_rubrica(request: Request, db: Session = Depends(get_db),
                       current_user: models.User = Depends(get_current_user), role_filter: Optional[str] = None):
    query = db.query(models.User).options(joinedload(models.User.roles))
    if role_filter:
        query = query.join(models.User.roles).filter(models.Role.name == role_filter)
    users = query.order_by(models.User.last_name, models.User.first_name).all()
    all_roles = db.query(models.Role).all()
    return templates.TemplateResponse("rubrica.html", {
        "request": request, "current_user": current_user, "users": users,
        "all_roles": all_roles, "current_filter": role_filter
    })

```

## File: `routers/__init__.py`

```python

```

## File: `routers/trainings.py`

```python
# File: routers/trainings.py
# Descrizione: Contiene le route per la gestione di allenamenti, calendario, turni e le relative API.

import uuid
from datetime import date, datetime, time, timedelta
from typing import List, Optional

from fastapi import APIRouter, Request, Depends, Form, Query, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session, joinedload
from dateutil.rrule import rrule, WEEKLY
from fastapi.templating import Jinja2Templates

import models
from database import get_db
from dependencies import get_current_user, get_current_admin_user
from utils import DAY_MAP_DATETIL, parse_orario, get_color_for_type

router = APIRouter(tags=["Allenamenti e Calendario"])
templates = Jinja2Templates(directory="templates")

# MODIFICA: Aggiornata la definizione dei gruppi per includere "Under 23"
TRAINING_GROUPS = {
    "Under 14": ["Allievo A", "Allievo B1", "Allievo B2", "Allievo C", "Cadetto"],
    "Over 14": ["Ragazzo", "Junior", "Under 23", "Senior"],
    "Master": ["Master"]
}
# Deriva dinamicamente tutte le categorie uniche dai gruppi
ALL_CATEGORIES = sorted(list(set(cat for sublist in TRAINING_GROUPS.values() for cat in sublist)))


@router.get("/calendario", response_class=HTMLResponse)
async def view_calendar(request: Request, current_user: models.User = Depends(get_current_user)):
    return templates.TemplateResponse("calendario.html", {"request": request, "current_user": current_user})


@router.get("/allenamenti", response_class=HTMLResponse)
async def list_allenamenti(
        request: Request, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user),
        filter: str = Query("future"), category_filter: List[str] = Query(None), tipo: Optional[str] = Query(None)
):
    today = date.today()
    query = db.query(models.Allenamento).options(joinedload(models.Allenamento.categories))

    if filter == "future":
        page_title = "Prossimi Allenamenti"
        query = query.filter(models.Allenamento.data >= today).order_by(models.Allenamento.data.asc(),
                                                                        models.Allenamento.orario.asc())
    elif filter == "past":
        page_title = "Allenamenti Passati"
        query = query.filter(models.Allenamento.data < today).order_by(models.Allenamento.data.desc(),
                                                                       models.Allenamento.orario.desc())
    else:
        page_title = "Tutti gli Allenamenti"
        query = query.order_by(models.Allenamento.data.desc())

    if category_filter:
        query = query.join(models.Allenamento.categories).filter(models.Category.name.in_(category_filter))
    if tipo:
        query = query.filter(models.Allenamento.tipo == tipo)

    allenamenti = query.distinct().all()
    all_types = [t[0] for t in db.query(models.Allenamento.tipo).distinct().all()]

    return templates.TemplateResponse("allenamenti_list.html", {
        "request": request, "allenamenti": allenamenti, "current_user": current_user,
        "page_title": page_title, "all_categories": ALL_CATEGORIES, "all_types": all_types,
        "current_filters": {"filter": filter, "category_filter": category_filter, "tipo": tipo}
    })


@router.get("/allenamenti/nuovo", response_class=HTMLResponse)
async def nuovo_allenamento_form(request: Request, admin_user: models.User = Depends(get_current_admin_user)):
    # Passa la struttura dei gruppi e tutte le categorie al template
    return templates.TemplateResponse("crea_allenamento.html", {
        "request": request, "current_user": admin_user,
        "training_groups": TRAINING_GROUPS, "all_categories": ALL_CATEGORIES
    })


@router.post("/allenamenti/nuovo", response_class=RedirectResponse)
async def crea_allenamento(
        request: Request, db: Session = Depends(get_db), admin_user: models.User = Depends(get_current_admin_user),
        tipo: str = Form(...), descrizione: Optional[str] = Form(None), data: date = Form(...),
        orario: str = Form(...), orario_personalizzato: Optional[str] = Form(None),
        is_recurring: Optional[str] = Form(None), giorni: Optional[List[str]] = Form(None),
        recurrence_count: Optional[int] = Form(None),
        category_names: List[str] = Form(...)
):
    final_orario_str = orario_personalizzato if orario == 'personalizzato' else orario

    selected_categories = db.query(models.Category).filter(models.Category.name.in_(category_names)).all()
    if len(selected_categories) != len(set(category_names)):
        # Potrebbe esserci un disallineamento se una categoria non esiste nel DB
        # Aggiungere qui una gestione dell'errore più robusta se necessario
        pass

    def create_single_allenamento(event_date, event_orario, rec_id=None):
        allenamento = models.Allenamento(
            tipo=tipo, descrizione=descrizione, data=event_date, orario=event_orario, recurrence_id=rec_id
        )
        allenamento.categories.extend(selected_categories)
        return allenamento

    if is_recurring == 'true':
        if not giorni or not recurrence_count or recurrence_count <= 0:
            # Gestione errore
            return templates.TemplateResponse("crea_allenamento.html", {"request": request,
                                                                        "error_message": "Per la ricorrenza, selezionare i giorni e un numero di occorrenze valido.",
                                                                        "current_user": admin_user}, status_code=400)

        byweekday_dateutil = [DAY_MAP_DATETIL[d] for d in giorni if d in DAY_MAP_DATETIL]
        start_dt_base, end_dt_base = parse_orario(data, final_orario_str)
        duration = end_dt_base - start_dt_base
        new_recurrence_id = str(uuid.uuid4())
        rule = rrule(WEEKLY, dtstart=start_dt_base, byweekday=byweekday_dateutil, count=recurrence_count)

        occurrences_to_save = []
        for occ_dt in rule:
            event_orario = f"{occ_dt.strftime('%H:%M')}-{(occ_dt + duration).strftime('%H:%M')}"
            occurrences_to_save.append(create_single_allenamento(occ_dt.date(), event_orario, new_recurrence_id))
        db.add_all(occurrences_to_save)
    else:
        nuovo_allenamento = create_single_allenamento(data, final_orario_str)
        db.add(nuovo_allenamento)

    db.commit()
    return RedirectResponse(url="/calendario", status_code=status.HTTP_303_SEE_OTHER)


# NUOVA ROTTA per mostrare il form di modifica precompilato
@router.get("/allenamenti/{id}/modifica", response_class=HTMLResponse)
async def modifica_allenamento_form(id: int, request: Request, db: Session = Depends(get_db),
                                    admin_user: models.User = Depends(get_current_admin_user)):
    allenamento = db.query(models.Allenamento).options(joinedload(models.Allenamento.categories)).filter(
        models.Allenamento.id == id).first()
    if not allenamento:
        raise HTTPException(status_code=404, detail="Allenamento non trovato")

    selected_category_names = [cat.name for cat in allenamento.categories]

    return templates.TemplateResponse("modifica_allenamento.html", {
        "request": request,
        "current_user": admin_user,
        "allenamento": allenamento,
        "selected_category_names": selected_category_names,
        "training_groups": TRAINING_GROUPS,
        "all_categories": ALL_CATEGORIES
    })


@router.post("/allenamenti/{id}/modifica", response_class=RedirectResponse)
async def aggiorna_allenamento(
        id: int, db: Session = Depends(get_db), admin_user: models.User = Depends(get_current_admin_user),
        tipo: str = Form(...), descrizione: Optional[str] = Form(None), data: date = Form(...),
        orario: str = Form(...), orario_personalizzato: Optional[str] = Form(None),
        category_names: List[str] = Form(...)
):
    allenamento = db.query(models.Allenamento).options(joinedload(models.Allenamento.categories)).filter(
        models.Allenamento.id == id).first()
    if not allenamento:
        raise HTTPException(status_code=404, detail="Allenamento non trovato")

    allenamento.tipo = tipo
    allenamento.descrizione = descrizione
    allenamento.data = data
    allenamento.orario = orario_personalizzato if orario == 'personalizzato' else orario

    # Aggiorna le categorie
    selected_categories = db.query(models.Category).filter(models.Category.name.in_(category_names)).all()
    allenamento.categories = selected_categories

    db.commit()
    return RedirectResponse(url="/calendario", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/allenamenti/delete", response_class=RedirectResponse)
async def delete_allenamento_events(
        db: Session = Depends(get_db), admin_user: models.User = Depends(get_current_admin_user),
        allenamento_id: int = Form(...), deletion_type: str = Form(...)
):
    allenamento = db.query(models.Allenamento).filter(models.Allenamento.id == allenamento_id).first()
    if not allenamento: raise HTTPException(status_code=404, detail="Allenamento non trovato")

    if deletion_type == 'future' and allenamento.recurrence_id:
        db.query(models.Allenamento).filter(models.Allenamento.recurrence_id == allenamento.recurrence_id,
                                            models.Allenamento.data >= allenamento.data).delete(
            synchronize_session=False)
    else:
        db.delete(allenamento)
    db.commit()
    return RedirectResponse(url="/calendario", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/turni", response_class=HTMLResponse)
async def view_turni(request: Request, db: Session = Depends(get_db),
                     admin_user: models.User = Depends(get_current_admin_user), week_offset: int = 0):
    today = date.today() + timedelta(weeks=week_offset)
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    allenatori = db.query(models.User).join(models.User.roles).filter(models.Role.name == 'allenatore').all()
    turni_settimana = db.query(models.Turno).filter(models.Turno.data.between(start_of_week, end_of_week)).order_by(
        models.Turno.data, models.Turno.fascia_oraria).all()
    return templates.TemplateResponse("turni.html", {
        "request": request, "current_user": admin_user, "allenatori": allenatori,
        "turni": turni_settimana, "week_offset": week_offset,
        "week_start": start_of_week, "week_end": end_of_week
    })


@router.post("/turni/assegna", response_class=RedirectResponse)
async def assegna_turno(
        db: Session = Depends(get_db), admin_user: models.User = Depends(get_current_admin_user),
        turno_id: int = Form(...), user_id: int = Form(...), week_offset: int = Form(0)
):
    turno = db.query(models.Turno).filter(models.Turno.id == turno_id).first()
    if not turno: raise HTTPException(status_code=404, detail="Turno non trovato")

    if user_id == 0:
        turno.user_id = None
    else:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user or not user.is_allenatore:
            raise HTTPException(status_code=400, detail="Utente non valido o non è un allenatore")
        turno.user_id = user.id
    db.commit()
    return RedirectResponse(url=f"/turni?week_offset={week_offset}", status_code=status.HTTP_303_SEE_OTHER)


# --- API Endpoints ---
@router.get("/api/training/groups")
async def get_training_groups(db: Session = Depends(get_db)):
    macro_groups = db.query(models.MacroGroup).options(joinedload(models.MacroGroup.subgroups)).all()
    return [{"id": mg.id, "name": mg.name, "subgroups": [{"id": sg.id, "name": sg.name} for sg in mg.subgroups]} for mg
            in macro_groups]


# --- API Endpoints ---
@router.get("/api/allenamenti")
async def get_allenamenti_api(
    db: Session = Depends(get_db),
    user_category: Optional[str] = Query(None),
    category_filter: List[str] = Query(None)
):
    query = db.query(models.Allenamento).options(joinedload(models.Allenamento.categories))

    if user_category:
        query = query.join(models.Allenamento.categories).filter(models.Category.name == user_category)
    elif category_filter:
        query = query.join(models.Allenamento.categories).filter(models.Category.name.in_(category_filter))

    allenamenti = query.distinct().all()
    formatted_events = []
    for a in allenamenti:
        start_dt, end_dt = parse_orario(a.data, a.orario)
        title = f"{a.tipo} - {a.descrizione}" if a.descrizione else a.tipo
        formatted_events.append({
            "id": a.id,
            "title": title,
            "start": start_dt.isoformat(),
            "end": end_dt.isoformat(),
            "backgroundColor": get_color_for_type(a.tipo),
            "borderColor": get_color_for_type(a.tipo),
            "extendedProps": {
                "descrizione": a.descrizione,
                "orario": a.orario,
                "recurrence_id": a.recurrence_id,
                # CORREZIONE: Assicura che le categorie siano passate come stringa
                "categories": ", ".join(sorted([cat.name for cat in a.categories]))
            }
        })
    return formatted_events

@router.get("/api/turni")
async def get_turni_api(db: Session = Depends(get_db)):
    turni = db.query(models.Turno).options(joinedload(models.Turno.user)).all()
    events = []
    for turno in turni:
        start_hour, end_hour = (8, 12) if turno.fascia_oraria == "Mattina" else (17, 21)
        start_dt = datetime.combine(turno.data, time(hour=start_hour))
        end_dt = datetime.combine(turno.data, time(hour=end_hour))
        title = f"{turno.user.first_name} {turno.user.last_name}" if turno.user else "Turno Libero"
        color = "#198754" if turno.user else "#dc3545"
        events.append({
            "id": turno.id, "title": title, "start": start_dt.isoformat(), "end": end_dt.isoformat(),
            "backgroundColor": color, "borderColor": color,
            "extendedProps": {"user_id": turno.user_id, "fascia_oraria": turno.fascia_oraria}
        })
    return events

```

## File: `routers/admin.py`

```python
# File: routers/admin.py
# Descrizione: Contiene le route per la sezione di amministrazione degli utenti.

from typing import List, Optional
from datetime import date, timedelta

from fastapi import APIRouter, Request, Depends, Form, Query, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from fastapi.templating import Jinja2Templates

import models
import security
from database import get_db
from dependencies import get_current_admin_user

router = APIRouter(prefix="/admin", tags=["Amministrazione"])
templates = Jinja2Templates(directory="templates")

# File: routers/admin.py

# File: routers/admin.py

# File: routers/admin.py

@router.get("/users", response_class=HTMLResponse)
async def admin_users_list(
        request: Request, db: Session = Depends(get_db), admin_user: models.User = Depends(get_current_admin_user),
        role_ids: List[int] = Query([]), categories: List[str] = Query([]),
        enrollment_year_str: Optional[str] = Query(None),
        cert_expiring: bool = Query(False),
        sort_by: str = Query("last_name"), sort_dir: str = Query("asc")
):
    query = db.query(models.User).options(joinedload(models.User.roles))

    enrollment_year = None
    if enrollment_year_str and enrollment_year_str.isdigit():
        enrollment_year = int(enrollment_year_str)

    # Applica i filtri
    if role_ids:
        query = query.join(models.user_roles).filter(models.user_roles.c.role_id.in_(role_ids))
    if enrollment_year:
        query = query.filter(models.User.enrollment_year == enrollment_year)
    if cert_expiring:
        two_months_from_now = date.today() + timedelta(days=60)
        query = query.filter(models.User.certificate_expiration <= two_months_from_now)

    # Applica l'ordinamento direttamente nella query SQL
    if sort_by == 'name':
        # Caso speciale per ordinare per cognome e poi nome
        order_logic = [models.User.last_name.desc(), models.User.first_name.desc()] if sort_dir == "desc" else [models.User.last_name.asc(), models.User.first_name.asc()]
        query = query.order_by(*order_logic)
    elif sort_by == 'certificate_expiration':
        # Ordinamento speciale: prima i certificati nulli o scaduti, poi per data
        order_logic = models.User.certificate_expiration.desc() if sort_dir == "desc" else models.User.certificate_expiration.asc()
        query = query.order_by(order_logic)
    else:
        sort_column = getattr(models.User, sort_by, models.User.last_name)
        if sort_dir == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

    users = query.all()

    if categories:
        users = [user for user in users if user.category in categories] [cite: 121]

    all_roles = db.query(models.Role).order_by(models.Role.name).all()
    all_years = sorted([y[0] for y in db.query(models.User.enrollment_year).distinct().all() if y[0] is not None], reverse=True)
    all_users_for_categories = db.query(models.User).options(joinedload(models.User.roles)).all()
    all_categories = sorted(list(set(u.category for u in all_users_for_categories if u.category and u.category != "N/D")))

    return templates.TemplateResponse("users_list.html", {
        "request": request, "users": users, "current_user": admin_user,
        "all_roles": all_roles, "all_categories": all_categories, "all_years": all_years,
        "current_filters": {"role_ids": role_ids, "categories": categories, "enrollment_year": enrollment_year, "cert_expiring": cert_expiring},
        "sort_by": sort_by, "sort_dir": sort_dir,
        "today": date.today()
    })
@router.get("/users/add", response_class=HTMLResponse)
async def admin_add_user_form(request: Request, db: Session = Depends(get_db),
                              admin_user: models.User = Depends(get_current_admin_user)):
    roles = db.query(models.Role).order_by(models.Role.name).all()
    return templates.TemplateResponse("user_add.html",
                                      {"request": request, "current_user": admin_user, "all_roles": roles, "user": {},
                                       "user_role_ids": set()})


# File: routers/admin.py

# File: routers/admin.py

@router.post("/users/add", response_class=RedirectResponse)
async def admin_add_user(db: Session = Depends(get_db), admin_user: models.User = Depends(get_current_admin_user),
                         # Campi Obbligatori
                         username: str = Form(...),
                         password: str = Form(...),
                         first_name: str = Form(...),
                         last_name: str = Form(...),
                         date_of_birth: date = Form(...),
                         roles_ids: List[int] = Form(...),
                         # Campi Opzionali (letti come stringhe per gestire i valori vuoti)
                         email: Optional[str] = Form(None),
                         phone_number: Optional[str] = Form(None),
                         tax_code: Optional[str] = Form(None),
                         enrollment_year_str: Optional[str] = Form(None),
                         membership_date_str: Optional[str] = Form(None),
                         certificate_expiration_str: Optional[str] = Form(None),
                         address: Optional[str] = Form(None),
                         manual_category: Optional[str] = Form(None)
                         ):
    # --- LOGICA DI CONVERSIONE E VALIDAZIONE ---
    # Converte i campi opzionali dal testo al tipo corretto (int, date) solo se non sono vuoti
    try:
        enrollment_year = int(enrollment_year_str) if enrollment_year_str else None
        membership_date = date.fromisoformat(membership_date_str) if membership_date_str else None
        certificate_expiration = date.fromisoformat(certificate_expiration_str) if certificate_expiration_str else None
    except ValueError:
        # Se la conversione fallisce (es. formato data non valido), ritorna un errore
        error_msg = "Formato data o numero non valido."
        return RedirectResponse(url=f"/admin/users/add?error={error_msg}", status_code=status.HTTP_303_SEE_OTHER)

    # Controlla se username o email (se fornita) esistono già
    if email and db.query(models.User).filter(models.User.email == email).first():
        error_msg = "Email già in uso."
        return RedirectResponse(url=f"/admin/users/add?error={error_msg}", status_code=status.HTTP_303_SEE_OTHER)

    if db.query(models.User).filter(models.User.username == username).first():
        error_msg = "Username già in uso."
        return RedirectResponse(url=f"/admin/users/add?error={error_msg}", status_code=status.HTTP_303_SEE_OTHER)

    if not roles_ids:
        error_msg = "È necessario selezionare almeno un ruolo."
        return RedirectResponse(url=f"/admin/users/add?error={error_msg}", status_code=status.HTTP_303_SEE_OTHER)

    # --- CREAZIONE UTENTE ---
    selected_roles = db.query(models.Role).filter(models.Role.id.in_(roles_ids)).all()
    new_user = models.User(
        username=username,
        hashed_password=security.get_password_hash(password),
        first_name=first_name,
        last_name=last_name,
        date_of_birth=date_of_birth,
        roles=selected_roles,
        # Campi opzionali convertiti
        email=email if email else None,
        phone_number=phone_number if phone_number else None,
        tax_code=tax_code if tax_code else None,
        enrollment_year=enrollment_year,
        membership_date=membership_date,
        certificate_expiration=certificate_expiration,
        address=address if address else None,
        manual_category=manual_category if manual_category else None
    )
    db.add(new_user)
    db.commit()
    return RedirectResponse(url="/admin/users?message=Utente creato con successo",
                            status_code=status.HTTP_303_SEE_OTHER)
@router.get("/users/{user_id}", response_class=HTMLResponse)
async def admin_view_user(user_id: int, request: Request, db: Session = Depends(get_db),
                          admin_user: models.User = Depends(get_current_admin_user)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user: raise HTTPException(status_code=404, detail="Utente non trovato")
    return templates.TemplateResponse("_user_detail.html",
                                      {"request": request, "user": user, "current_user": admin_user})


@router.get("/users/{user_id}/edit", response_class=HTMLResponse)
async def admin_edit_user_form(user_id: int, request: Request, db: Session = Depends(get_db),
                               admin_user: models.User = Depends(get_current_admin_user)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user: raise HTTPException(status_code=404, detail="Utente non trovato")
    roles = db.query(models.Role).all()
    user_role_ids = {role.id for role in user.roles}
    return templates.TemplateResponse("_user_edit.html",
                                      {"request": request, "user": user, "current_user": admin_user, "all_roles": roles,
                                       "user_role_ids": user_role_ids})


@router.post("/users/{user_id}/edit", response_class=RedirectResponse)
async def admin_edit_user(user_id: int, db: Session = Depends(get_db),
                          admin_user: models.User = Depends(get_current_admin_user),
                          first_name: str = Form(...), last_name: str = Form(...), email: str = Form(...),
                          date_of_birth: date = Form(...), roles_ids: List[int] = Form([]),
                          phone_number: Optional[str] = Form(None), tax_code: Optional[str] = Form(None),
                          enrollment_year: Optional[int] = Form(None), membership_date: Optional[date] = Form(None),
                          certificate_expiration: Optional[date] = Form(None), address: Optional[str] = Form(None),
                          manual_category: Optional[str] = Form(None), password: Optional[str] = Form(None)
                          ):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user: raise HTTPException(status_code=404, detail="Utente non trovato")
    user.first_name, user.last_name, user.email = first_name, last_name, email
    user.date_of_birth = date_of_birth
    user.phone_number, user.tax_code = phone_number, tax_code
    user.enrollment_year, user.membership_date = enrollment_year, membership_date
    user.certificate_expiration, user.address = certificate_expiration, address
    user.manual_category = manual_category if manual_category else None
    if password:
        user.hashed_password = security.get_password_hash(password)
    selected_roles = db.query(models.Role).filter(models.Role.id.in_(roles_ids)).all()
    user.roles = selected_roles
    db.commit()
    return RedirectResponse(url=f"/admin/users/{user_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/users/{user_id}/delete", response_class=RedirectResponse)
async def admin_delete_user(user_id: int, db: Session = Depends(get_db),
                            admin_user: models.User = Depends(get_current_admin_user)):
    if user_id == admin_user.id:
        return RedirectResponse(url="/admin/users?error=Non puoi eliminare te stesso.",
                                status_code=status.HTTP_303_SEE_OTHER)
    user_to_delete = db.query(models.User).filter(models.User.id == user_id).first()
    if user_to_delete:
        db.delete(user_to_delete)
        db.commit()
    return RedirectResponse(url="/admin/users?message=Utente eliminato.", status_code=status.HTTP_303_SEE_OTHER)

```

## File: `routers/authentication.py`

```python
# File: routers/authentication.py
# Descrizione: Contiene le route per la gestione dell'autenticazione: login e logout.

from fastapi import APIRouter, Request, Depends, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

import models
import security
from database import get_db

router = APIRouter(tags=["Autenticazione"])
templates = Jinja2Templates(directory="templates")


@router.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login", response_class=RedirectResponse)
async def login(
    request: Request,
    db: Session = Depends(get_db),
    username: str = Form(...),
    password: str = Form(...)
):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user or not security.verify_password(password, user.hashed_password):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error_message": "Username o password non validi"},
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    request.session["user_id"] = user.id
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/logout", response_class=RedirectResponse)
async def logout(request: Request):
    request.session.pop("user_id", None)
    return RedirectResponse(url="/login?message=Logout effettuato", status_code=status.HTTP_303_SEE_OTHER)

```

## File: `routers/resources.py`

```python
# File: routers/resources.py
# Descrizione: Contiene le route per la gestione delle risorse (barche e pesi).

from typing import List, Optional
from fastapi import APIRouter, Request, Depends, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session, joinedload
from fastapi.templating import Jinja2Templates

import models
from database import get_db
from dependencies import get_current_user, get_current_admin_user

router = APIRouter(prefix="/risorse", tags=["Risorse"])
templates = Jinja2Templates(directory="templates")


@router.get("/barche", response_class=HTMLResponse)
async def list_barche(request: Request, db: Session = Depends(get_db),
                      current_user: models.User = Depends(get_current_user), tipo_filter: Optional[str] = None):
    query = db.query(models.Barca)
    if tipo_filter:
        query = query.filter(models.Barca.tipo == tipo_filter)
    barche = query.order_by(models.Barca.nome).all()
    tipi_barca = db.query(models.Barca.tipo).distinct().order_by(models.Barca.tipo).all()
    return templates.TemplateResponse("barche_list.html", {
        "request": request, "current_user": current_user, "barche": barche,
        "tipi_barca": [t[0] for t in tipi_barca], "current_filter": tipo_filter
    })


@router.get("/barche/nuova", response_class=HTMLResponse)
async def nuova_barca_form(request: Request, db: Session = Depends(get_db),
                           admin_user: models.User = Depends(get_current_admin_user)):
    atleti = db.query(models.User).join(models.User.roles).filter(models.Role.name == 'atleta').order_by(
        models.User.last_name).all()
    return templates.TemplateResponse("crea_barca.html",
                                      {"request": request, "current_user": admin_user, "atleti": atleti})


@router.post("/barche/nuova", response_class=RedirectResponse)
async def crea_barca(
        db: Session = Depends(get_db), admin_user: models.User = Depends(get_current_admin_user),
        nome: str = Form(...), tipo: str = Form(...), costruttore: Optional[str] = Form(None),
        anno: Optional[int] = Form(None), remi_assegnati: Optional[str] = Form(None),
        atleti_ids: List[int] = Form([]),
        altezza_scalmi: Optional[float] = Form(None), altezza_carrello: Optional[float] = Form(None),
        apertura_totale: Optional[float] = Form(None), semiapertura_sx: Optional[float] = Form(None)
):
    atleti_assegnati = db.query(models.User).filter(models.User.id.in_(atleti_ids)).all()
    nuova_barca = models.Barca(
        nome=nome, tipo=tipo, costruttore=costruttore, anno=anno,
        remi_assegnati=remi_assegnati, atleti_assegnati=atleti_assegnati,
        altezza_scalmi=altezza_scalmi, altezza_carrello=altezza_carrello,
        apertura_totale=apertura_totale, semiapertura_sx=semiapertura_sx
    )
    db.add(nuova_barca)
    db.commit()
    return RedirectResponse(url="/risorse/barche", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/barche/{barca_id}/modifica", response_class=HTMLResponse)
async def modifica_barca_form(barca_id: int, request: Request, db: Session = Depends(get_db),
                              admin_user: models.User = Depends(get_current_admin_user)):
    barca = db.query(models.Barca).options(joinedload(models.Barca.atleti_assegnati)).filter(
        models.Barca.id == barca_id).first()
    if not barca: raise HTTPException(status_code=404, detail="Barca non trovata")
    atleti = db.query(models.User).join(models.User.roles).filter(models.Role.name == 'atleta').order_by(
        models.User.last_name).all()
    assigned_atleta_ids = {atleta.id for atleta in barca.atleti_assegnati}
    return templates.TemplateResponse("modifica_barca.html",
                                      {"request": request, "current_user": admin_user, "barca": barca, "atleti": atleti,
                                       "assigned_atleta_ids": assigned_atleta_ids})


@router.post("/barche/{barca_id}/modifica", response_class=RedirectResponse)
async def aggiorna_barca(
        barca_id: int, db: Session = Depends(get_db), admin_user: models.User = Depends(get_current_admin_user),
        nome: str = Form(...), tipo: str = Form(...), costruttore: Optional[str] = Form(None),
        anno: Optional[int] = Form(None), remi_assegnati: Optional[str] = Form(None),
        atleti_ids: List[int] = Form([]),
        altezza_scalmi: Optional[float] = Form(None), altezza_carrello: Optional[float] = Form(None),
        apertura_totale: Optional[float] = Form(None), semiapertura_sx: Optional[float] = Form(None)
):
    barca = db.query(models.Barca).filter(models.Barca.id == barca_id).first()
    if not barca: raise HTTPException(status_code=404, detail="Barca non trovata")
    barca.nome, barca.tipo, barca.costruttore, barca.anno = nome, tipo, costruttore, anno
    barca.remi_assegnati = remi_assegnati
    barca.altezza_scalmi, barca.altezza_carrello = altezza_scalmi, altezza_carrello
    barca.apertura_totale, barca.semiapertura_sx = apertura_totale, semiapertura_sx
    atleti_assegnati = db.query(models.User).filter(models.User.id.in_(atleti_ids)).all()
    barca.atleti_assegnati = atleti_assegnati
    db.commit()
    return RedirectResponse(url="/risorse/barche", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/barche/{barca_id}/elimina", response_class=RedirectResponse)
async def elimina_barca(barca_id: int, db: Session = Depends(get_db),
                        admin_user: models.User = Depends(get_current_admin_user)):
    barca = db.query(models.Barca).filter(models.Barca.id == barca_id).first()
    if not barca: raise HTTPException(status_code=404, detail="Barca non trovata")
    db.delete(barca)
    db.commit()
    return RedirectResponse(url="/risorse/barche", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/pesi", response_class=HTMLResponse)
async def view_pesi(request: Request, db: Session = Depends(get_db),
                    current_user: models.User = Depends(get_current_user), atleta_id: Optional[int] = None):
    esercizi = db.query(models.EsercizioPesi).order_by(models.EsercizioPesi.ordine).all()
    atleti = db.query(models.User).join(models.User.roles).filter(models.Role.name == 'atleta').order_by(
        models.User.last_name).all()
    scheda_data = {}
    selected_atleta = None
    if current_user.is_admin or current_user.is_allenatore:
        if atleta_id:
            selected_atleta = db.query(models.User).filter(models.User.id == atleta_id).first()
    elif current_user.is_atleta:
        selected_atleta = current_user

    if selected_atleta:
        schede = db.query(models.SchedaPesi).filter(models.SchedaPesi.atleta_id == selected_atleta.id).all()
        scheda_data = {s.esercizio_id: s for s in schede}

    return templates.TemplateResponse("pesi.html",
                                      {"request": request, "current_user": current_user, "esercizi": esercizi,
                                       "atleti": atleti, "selected_atleta": selected_atleta,
                                       "scheda_data": scheda_data})


@router.post("/pesi/update", response_class=RedirectResponse)
async def update_scheda_pesi(request: Request, db: Session = Depends(get_db),
                             current_user: models.User = Depends(get_current_user)):
    form_data = await request.form()
    atleta_id = int(form_data.get("atleta_id"))
    if not (current_user.is_admin or current_user.is_allenatore or current_user.id == atleta_id):
        raise HTTPException(status_code=403, detail="Non autorizzato")

    for key, value in form_data.items():
        if key.startswith("massimale_"):
            esercizio_id = int(key.split("_")[1])
            scheda = db.query(models.SchedaPesi).filter_by(atleta_id=atleta_id, esercizio_id=esercizio_id).first()
            if not scheda:
                scheda = models.SchedaPesi(atleta_id=atleta_id, esercizio_id=esercizio_id)
                db.add(scheda)
            scheda.massimale = float(value) if value else None
            scheda.carico_5_rep = float(form_data.get(f"5rep_{esercizio_id}")) if form_data.get(
                f"5rep_{esercizio_id}") else None
            scheda.carico_7_rep = float(form_data.get(f"7rep_{esercizio_id}")) if form_data.get(
                f"7rep_{esercizio_id}") else None
            scheda.carico_10_rep = float(form_data.get(f"10rep_{esercizio_id}")) if form_data.get(
                f"10rep_{esercizio_id}") else None
            scheda.carico_20_rep = float(form_data.get(f"20rep_{esercizio_id}")) if form_data.get(
                f"20rep_{esercizio_id}") else None

    db.commit()
    return RedirectResponse(url=f"/risorse/pesi?atleta_id={atleta_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/pesi/add_esercizio", response_class=RedirectResponse)
async def add_esercizio_pesi(db: Session = Depends(get_db), admin_user: models.User = Depends(get_current_admin_user),
                             nome: str = Form(...), ordine: int = Form(...)):
    new_esercizio = models.EsercizioPesi(nome=nome, ordine=ordine)
    db.add(new_esercizio)
    db.commit()
    return RedirectResponse(url="/risorse/pesi", status_code=status.HTTP_303_SEE_OTHER)

```

