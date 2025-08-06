# File: routers/users.py
from typing import Optional
from datetime import date
from fastapi import APIRouter, Request, Depends, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session, joinedload
from fastapi.templating import Jinja2Templates
from app.database.database import get_db
from app import models
from app.security import security
from app.database.database import get_db
from app.dependencies.dependencies import get_current_user
from app.dependencies.dependencies import templates

from app.dependencies.dependencies import templates, get_current_user, get_db

@router.get("/dashboard")
async def dashboard(request: Request, db: Session = Depends(get_db),
                    current_user: models.User = Depends(get_current_user)):
    return templates.TemplateResponse("dashboard.html", {"request": request, ...})


router = APIRouter(tags=["Utenti e Pagine Principali"])
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=RedirectResponse, include_in_schema=False)
async def root(request: Request):
    return RedirectResponse(url="/login" if not request.session.get("user_id") else "/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    today = date.today()
    dashboard_data = {}
    if current_user.is_allenatore:
        dashboard_data['prossimi_turni'] = db.query(models.Turno).filter(models.Turno.user_id == current_user.id, models.Turno.data >= today).order_by(models.Turno.data).limit(3).all()
    if current_user.is_atleta:
        subgroups = db.query(models.SubGroup).filter(models.SubGroup.name == current_user.category).all()
        if subgroups:
            subgroup_ids = [sg.id for sg in subgroups]
            dashboard_data['prossimi_allenamenti'] = db.query(models.Allenamento).join(models.allenamento_subgroup_association).filter(models.allenamento_subgroup_association.c.subgroup_id.in_(subgroup_ids), models.Allenamento.data >= today).order_by(models.Allenamento.data).limit(3).all()
    return templates.TemplateResponse("dashboard.html", {"request": request, "current_user": current_user, "dashboard_data": dashboard_data})

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