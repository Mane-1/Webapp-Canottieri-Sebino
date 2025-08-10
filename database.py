# File: database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
from fastapi import HTTPException, status

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
    """Yield a database session and ensure proper cleanup.

    In case the database connection cannot be established (for example when the
    DB server is down), we raise an HTTP 503 error.  The global exception
    handlers will translate this into either a JSON or HTML response depending
    on the request type.
    """

    try:
        db = SessionLocal()
    except OperationalError as exc:  # pragma: no cover - exercised in tests
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
        ) from exc

    try:
        yield db
    except OperationalError as exc:  # pragma: no cover
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
        ) from exc
    finally:
        db.close()
