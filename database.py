# File: database.py
import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
from fastapi import HTTPException, status
try:  # pragma: no cover - fallback if python-dotenv missing
    from dotenv import load_dotenv
except ModuleNotFoundError:  # pragma: no cover
    def load_dotenv():
        return False

load_dotenv()

# Configura il logger
logger = logging.getLogger("db")
logger.setLevel(logging.INFO)

# Recupera DATABASE_URL dall'ambiente, default SQLite se assente
SQLALCHEMY_DATABASE_URL = os.environ.get(
    "DATABASE_URL", "sqlite:///./canottierisebino.db"
)

# Logga l'URL (ATTENZIONE: maschera la password!)
safe_url = SQLALCHEMY_DATABASE_URL.replace(
    SQLALCHEMY_DATABASE_URL.split("@")[0], "****"
) if "@" in SQLALCHEMY_DATABASE_URL else SQLALCHEMY_DATABASE_URL
logger.info(f"Sto usando il database: {safe_url}")

# Correggi prefisso postgres:// → postgresql://
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace(
        "postgres://", "postgresql://"
    )

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in SQLALCHEMY_DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Yield a database session and ensure proper cleanup."""
    try:
        db = SessionLocal()
    except OperationalError as exc:
        logger.error(f"Errore di connessione al DB: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
        ) from exc

    try:
        yield db
    except OperationalError as exc:
        logger.error(f"Errore durante l'uso del DB: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
        ) from exc
    finally:
        db.close()
