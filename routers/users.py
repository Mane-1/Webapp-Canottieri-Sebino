# File: routers/users.py
from typing import Optional
from datetime import date, datetime, time
from fastapi import APIRouter, Request, Depends, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session, joinedload
from fastapi.templating import Jinja2Templates
import models, security
from database import get_db
from dependencies import get_current_user
from utils import parse_orario, get_color_for_type
from services.attendance_service import compute_status_for_athlete

router = APIRouter(tags=["Utenti e Pagine Principali"])
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=RedirectResponse, include_in_schema=False)
async def root(request: Request):
    return RedirectResponse(url="/login" if not request.session.get("user_id") else "/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    today = date.today()
    events = []

    if current_user.is_atleta:
        allenamenti = (
            db.query(models.Allenamento)
            .join(models.Allenamento.categories)
            .options(
                joinedload(models.Allenamento.categories),
                joinedload(models.Allenamento.coaches),
            )
            .filter(
                models.Categoria.nome == current_user.category,
                models.Allenamento.data >= today,
            )
            .order_by(models.Allenamento.data, models.Allenamento.orario)
            .all()
        )
        for a in allenamenti:
            start_dt, end_dt = parse_orario(a.data, a.orario)
            events.append(
                {
                    "id": a.id,
                    "type": "allenamento",
                    "title": f"{a.tipo} - {a.descrizione}" if a.descrizione else a.tipo,
                    "date": a.data,
                    "start": start_dt,
                    "end": end_dt,
                    "color": get_color_for_type(a.tipo),
                    "description": a.descrizione or "Nessuna descrizione.",
                    "categories": ", ".join(c.nome for c in a.categories) if a.categories else "Nessuna",
                    "coaches": ", ".join(f"{c.first_name} {c.last_name}" for c in a.coaches) if a.coaches else "Nessuno",
                    "recurrence": "Sì" if a.recurrence_id else "No",
                    "status": compute_status_for_athlete(db, a.id, current_user.id).value,
                }
            )

    if current_user.is_allenatore:
        turni = (
            db.query(models.Turno)
            .filter(models.Turno.user_id == current_user.id, models.Turno.data >= today)
            .order_by(models.Turno.data, models.Turno.fascia_oraria)
            .all()
        )
        for t in turni:
            start_hour, end_hour = (8, 12) if t.fascia_oraria == "Mattina" else (17, 21)
            start_dt = datetime.combine(t.data, time(hour=start_hour))
            end_dt = datetime.combine(t.data, time(hour=end_hour))
            events.append(
                {
                    "id": t.id,
                    "type": "turno",
                    "title": f"Turno {t.fascia_oraria}",
                    "date": t.data,
                    "start": start_dt,
                    "end": end_dt,
                    "fascia": t.fascia_oraria,
                    "description": f"Turno {t.fascia_oraria}",
                }
            )

        allenamenti_coach = (
            db.query(models.Allenamento)
            .join(models.Allenamento.coaches)
            .options(
                joinedload(models.Allenamento.categories),
                joinedload(models.Allenamento.coaches),
            )
            .filter(models.User.id == current_user.id, models.Allenamento.data >= today)
            .order_by(models.Allenamento.data, models.Allenamento.orario)
            .all()
        )
        for a in allenamenti_coach:
            start_dt, end_dt = parse_orario(a.data, a.orario)
            events.append(
                {
                    "id": a.id,
                    "type": "allenamento",
                    "title": f"{a.tipo} - {a.descrizione}" if a.descrizione else a.tipo,
                    "date": a.data,
                    "start": start_dt,
                    "end": end_dt,
                    "color": get_color_for_type(a.tipo),
                    "description": a.descrizione or "Nessuna descrizione.",
                    "categories": ", ".join(c.nome for c in a.categories) if a.categories else "Nessuna",
                    "coaches": ", ".join(f"{c.first_name} {c.last_name}" for c in a.coaches) if a.coaches else "Nessuno",
                    "recurrence": "Sì" if a.recurrence_id else "No",
                }
            )

    events.sort(key=lambda e: e["start"])
    events = events[:5]

    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "current_user": current_user, "events": events},
    )

@router.get("/profilo", response_class=HTMLResponse)
async def view_profile(request: Request, current_user: models.User = Depends(get_current_user)):
    return templates.TemplateResponse("profilo/profilo.html", {"request": request, "user": current_user, "current_user": current_user})

@router.get("/profilo/modifica", response_class=HTMLResponse)
async def edit_profile_form(request: Request, current_user: models.User = Depends(get_current_user)):
    return templates.TemplateResponse("profilo/profilo_modifica.html", {"request": request, "user": current_user, "current_user": current_user})

@router.post("/profilo/modifica", response_class=RedirectResponse)
async def update_profile(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user), email: Optional[str] = Form(None), phone_number: Optional[str] = Form(None), new_password: Optional[str] = Form(None)):
    current_user.email = email
    current_user.phone_number = phone_number
    if new_password: current_user.hashed_password = security.get_password_hash(new_password)
    db.commit()
    return RedirectResponse(url="/profilo?message=Profilo aggiornato con successo", status_code=303)

@router.get("/rubrica", response_class=HTMLResponse)
async def view_rubrica(request: Request, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user), role_filter: Optional[str] = None):
    query = db.query(models.User).options(joinedload(models.User.roles))
    if role_filter: query = query.join(models.User.roles).filter(models.Role.name == role_filter)
    users = query.order_by(models.User.last_name, models.User.first_name).all()
    all_roles = db.query(models.Role).all()
    return templates.TemplateResponse("rubrica.html", {"request": request, "current_user": current_user, "users": users, "all_roles": all_roles, "current_filter": role_filter})
