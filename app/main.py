# app/main.py

import os
import logging
from datetime import date

from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.models import models
from app.security.security import get_password_hash
from app.database.database import engine, Base, SessionLocal
from app.utils.utils import get_color_for_type
from app.routers import authentication, users, trainings, resources, admin

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Istanza FastAPI
app = FastAPI(title="Gestionale Canottieri")

# Secret key per le sessioni
SECRET_KEY = os.environ.get('SECRET_KEY', 'un-segreto-di-default-non-sicuro')
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Templates e file statici
templates = Jinja2Templates(directory="templates")
templates.env.globals['get_color_for_type'] = get_color_for_type
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.on_event("startup")
def on_startup():
    """
    1. Crea tutte le tabelle se non esistono.
    2. Popola i ruoli e l'utente admin se il DB è vuoto.
    """
    logger.info("Avvio dell'applicazione in corso...")
    Base.metadata.create_all(bind=engine)
    logger.info("Tabelle verificate/creati.")

    db = SessionLocal()
    try:
        # Popola Ruoli se vuoti
        if db.query(models.Role).count() == 0:
            logger.info("Popolamento ruoli iniziale...")
            db.add_all([
                models.Role(name='atleta'),
                models.Role(name='allenatore'),
                models.Role(name='admin')
            ])
            db.commit()

        # Crea utente admin 'gabriele' se non esiste
        if not db.query(models.User).filter(models.User.username == "gabriele").first():
            logger.info("Creazione utente admin di default...")
            admin_role = db.query(models.Role).filter_by(name='admin').one()
            allenatore_role = db.query(models.Role).filter_by(name='allenatore').one()
            admin_user = models.User(
                username="gabriele",
                hashed_password=get_password_hash("manenti"),
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
        logger.error(f"Errore during startup seeding: {e}")
        db.rollback()
    finally:
        db.close()


# Inclusione router modulari
app.include_router(authentication.router)
app.include_router(users.router)
app.include_router(trainings.router)
app.include_router(resources.router)
app.include_router(admin.router)
