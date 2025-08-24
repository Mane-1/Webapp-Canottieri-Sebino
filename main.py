# File: main.py
# Descrizione: File principale dell'applicazione. Inizializza FastAPI, configura middleware,
# template, file statici, eventi di startup e include i router modulari.

import os
import logging
import logging.config
from contextlib import asynccontextmanager
from datetime import date
try:  # pragma: no cover - fallback if python-dotenv is missing
    from dotenv import load_dotenv
except ModuleNotFoundError:  # pragma: no cover
    def load_dotenv():
        return False

load_dotenv()

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError
from starlette.middleware.sessions import SessionMiddleware

# Importa i moduli del progetto
from models import *
import security
from database import engine, Base, SessionLocal
from utils import get_color_for_type, render
from routers import (
    authentication,
    users,
    trainings_stats,
    trainings,
    resources,
    admin,
    trainings_calendar,
    availabilities,
    attendance,
    athletes,
    calendar as calendar_router,
    activities,
    api_activities,
)
from seed import seed_categories, seed_turni, seed_default_allenamenti, seed_mezzi

# Configurazione del logging tramite dictConfig
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
logging.config.dictConfig(
    {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s %(levelname)s %(name)s: %(message)s",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "standard",
            }
        },
        "root": {"level": LOG_LEVEL, "handlers": ["console"]},
    }
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestione del ciclo di vita dell'applicazione."""
    logger.info("Avvio dell'applicazione in corso...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Verifica tabelle completata.")
    except Exception as e:  # pragma: no cover
        logger.error(f"Impossibile connettersi al database all'avvio: {e}")
        yield
        return

    db = SessionLocal()
    try:
        if db.query(Role).count() == 0:
            logger.info("Popolamento dei ruoli...")
            db.add_all([
                Role(name='atleta'),
                Role(name='allenatore'),
                Role(name='istruttore'),
                Role(name='admin')
            ])
            db.commit()

        seed_categories(db)
        seed_turni(db)
        seed_default_allenamenti(db)
        seed_mezzi(db)

        admin_username = os.environ.get("ADMIN_USERNAME", "admin")
        admin_password = os.environ.get("ADMIN_PASSWORD")
        if admin_password and not db.query(User).filter(User.username == admin_username).first():
            logger.info(f"Creazione utente admin '{admin_username}'...")
            admin_role = db.query(Role).filter_by(name='admin').one()
            allenatore_role = db.query(Role).filter_by(name='allenatore').one()
            admin_user = User(
                username=admin_username,
                hashed_password=security.get_password_hash(admin_password),
                first_name="Admin",
                last_name="User",
                email=os.environ.get("ADMIN_EMAIL", "admin@example.com"),
                date_of_birth=date(1990, 1, 1),
                roles=[admin_role, allenatore_role]
            )
            db.add(admin_user)
            db.commit()
            logger.info(f"Utente admin '{admin_username}' creato.")
    except Exception as e:
        logger.warning(
            f"Errore durante il popolamento dei dati di base all'avvio: {e}"
        )
        db.rollback()
    finally:
        db.close()

    yield


# Creazione dell'istanza FastAPI
app = FastAPI(title="Gestionale Canottieri", lifespan=lifespan)

# Configurazione del middleware per le sessioni
SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable is required")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Configurazione dei template Jinja2 e dei file statici
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates.env.globals['get_color_for_type'] = get_color_for_type


def is_api_request(request: Request) -> bool:
    """Return ``True`` if the incoming request expects a JSON response."""
    accept = request.headers.get("accept", "")
    return "application/json" in accept or request.url.path.startswith("/api")


# Evento di startup dell'applicazione
# Inclusione dei router modulari
# Ogni router gestisce una sezione specifica dell'applicazione
app.include_router(authentication.router)
app.include_router(users.router)
app.include_router(trainings_stats.router)
app.include_router(trainings.router)
app.include_router(trainings_calendar.router)
app.include_router(resources.router)
app.include_router(resources.mezzi_router, prefix="/mezzi")
app.include_router(admin.router)
app.include_router(availabilities.router)
app.include_router(attendance.router)
app.include_router(athletes.router)
app.include_router(calendar_router.router)
app.include_router(activities.router)
app.include_router(api_activities.router)


@app.get("/health")
@app.head("/health")
async def health() -> dict:
    """Semplice endpoint di health-check."""
    return {"status": "ok"}


@app.get("/__version__")
async def version() -> dict:
    return {"version": os.environ.get("GIT_COMMIT", "unknown")}


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == status.HTTP_404_NOT_FOUND:
        if is_api_request(request):
            return JSONResponse({"detail": "Not Found"}, status_code=exc.status_code)
        return render(request, "errors/404.html", status_code=exc.status_code, ctx={})
    if exc.status_code == status.HTTP_503_SERVICE_UNAVAILABLE:
        if is_api_request(request):
            return JSONResponse(
                {"detail": exc.detail or "Service Unavailable"},
                status_code=exc.status_code,
            )
        return render(request, "errors/503.html", status_code=exc.status_code, ctx={})
    return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    if is_api_request(request):
        return JSONResponse(
            {"detail": exc.errors()},
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
    return render(
        request,
        "errors/404.html",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        ctx={},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error", exc_info=exc)
    if is_api_request(request):
        return JSONResponse(
            {"detail": "Internal Server Error"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    try:
        return render(
            request,
            "errors/500.html",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            ctx={},
        )
    except Exception:
        return PlainTextResponse(
            "Internal Server Error",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@app.get('/manifest.webmanifest')
async def manifest():
    return FileResponse('static/manifest.webmanifest', media_type='application/manifest+json')

@app.get('/sw.js')
async def service_worker():
    return FileResponse('static/sw.js', media_type='application/javascript')


