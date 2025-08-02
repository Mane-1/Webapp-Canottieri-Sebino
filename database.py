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
