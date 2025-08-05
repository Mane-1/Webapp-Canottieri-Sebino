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
