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

app = FastAPI(title="Gestionale Canottieri")

# Carica la SECRET_KEY da env var
SECRET_KEY = os.getenv("SECRET_KEY", "un-segreto-di-default-non-sicuro")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Templates e static files
templates = Jinja2Templates(directory="templates")
templates.env.globals['get_color_for_type'] = get_color_for_type
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
def on_startup():
    logger.info("Avvio dell'applicazione…")
    # Crea tabelle
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Seed ruoli
        if db.query(models.Role).count() == 0:
            db.add_all([
                models.Role(name='atleta'),
                models.Role(name='allenatore'),
                models.Role(name='admin'),
            ])
            db.commit()
        # Seed admin user
        if not db.query(models.User).filter(models.User.username=='gabriele').first():
            admin_role = db.query(models.Role).filter_by(name='admin').one()
            allen_role = db.query(models.Role).filter_by(name='allenatore').one()
            admin = models.User(
                username="gabriele",
                hashed_password=get_password_hash("manenti"),
                first_name="Gabriele",
                last_name="Manenti",
                email="gabriele.manenti@example.com",
                date_of_birth=date(1990,1,1),
                roles=[admin_role, allen_role],
            )
            db.add(admin)
            db.commit()
    except:
        db.rollback()
    finally:
        db.close()

# Include router
app.include_router(authentication.router)
app.include_router(users.router)
app.include_router(trainings.router)
app.include_router(resources.router)
app.include_router(admin.router)
