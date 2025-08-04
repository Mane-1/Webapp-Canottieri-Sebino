# File: main.py
# File principale dell'applicazione FastAPI. Contiene la configurazione, le route e la logica di business.

import os
import logging
import uuid
from datetime import date, datetime, timedelta, time
from typing import List, Optional

from fastapi import FastAPI, Request, Form, Depends, HTTPException, status, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from starlette.middleware.sessions import SessionMiddleware
from dateutil.rrule import rrule, WEEKLY, MO, TU, WE, TH, FR, SA, SU

from database import engine, Base, get_db
import models
import security

# Configurazione
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = FastAPI()

SECRET_KEY = os.environ.get('SECRET_KEY', 'un-segreto-di-default-non-sicuro')
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


# ===== Funzioni di supporto =====
def get_color_for_type(training_type: Optional[str]) -> str:
    colors = {"Barca": "#0d6efd", "Remoergometro": "#198754", "Corsa": "#6f42c1", "Pesi": "#dc3545",
              "Circuito": "#fd7e14", "Altro": "#212529"}
    return colors.get(training_type, "#6c757d")


templates.env.globals['get_color_for_type'] = get_color_for_type

DAY_MAP_DATETIL = {"Lunedì": MO, "Martedì": TU, "Mercoledì": WE, "Giovedì": TH, "Venerdì": FR, "Sabato": SA,
                   "Domenica": SU}


def parse_time_string(time_str: str) -> time:
    try:
        hour, minute = map(int, time_str.split(':'))
        return time(hour, minute)
    except (ValueError, TypeError):
        return time(0, 0)


def parse_orario(base_date: date, orario_str: str) -> tuple[datetime, datetime]:
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


# ===== Funzione di startup =====
@app.on_event("startup")
def on_startup():
    logger.info("Avvio dell'applicazione in corso...")
    Base.metadata.create_all(bind=engine)
    logger.info("Verifica tabelle completata.")


# ===== Dipendenze per l'Autenticazione =====
async def get_current_user(request: Request, db: Session = Depends(get_db)) -> models.User:
    user_id = request.session.get("user_id")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_303_SEE_OTHER, detail="Non autenticato",
                            headers={"Location": "/login"})
    user = db.query(models.User).options(joinedload(models.User.roles)).filter(models.User.id == user_id).first()
    if user is None:
        request.session.pop("user_id", None)
        raise HTTPException(status_code=status.HTTP_303_SEE_OTHER, detail="Utente non trovato",
                            headers={"Location": "/login"})
    return user


async def get_current_admin_user(current_user: models.User = Depends(get_current_user)) -> models.User:
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accesso negato.")
    return current_user


# ===== Route Principali =====
@app.get("/", response_class=RedirectResponse)
async def root(request: Request):
    if request.session.get("user_id"):
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/dashboard", response_class=HTMLResponse)
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


@app.get("/profilo", response_class=HTMLResponse)
async def view_profile(request: Request, current_user: models.User = Depends(get_current_user)):
    return templates.TemplateResponse("profilo.html",
                                      {"request": request, "user": current_user, "current_user": current_user})


@app.get("/profilo/modifica", response_class=HTMLResponse)
async def edit_profile_form(request: Request, current_user: models.User = Depends(get_current_user)):
    return templates.TemplateResponse("profilo_modifica.html",
                                      {"request": request, "user": current_user, "current_user": current_user})


@app.post("/profilo/modifica", response_class=RedirectResponse)
async def update_profile(
        db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user),
        email: Optional[str] = Form(None), phone_number: Optional[str] = Form(None),
        new_password: Optional[str] = Form(None)
):
    current_user.email = email
    current_user.phone_number = phone_number
    if new_password:
        current_user.hashed_password = security.get_password_hash(new_password)
    db.commit()
    return RedirectResponse(url="/profilo?message=Profilo aggiornato con successo",
                            status_code=status.HTTP_303_SEE_OTHER)


@app.get("/calendario", response_class=HTMLResponse)
async def view_calendar(request: Request, current_user: models.User = Depends(get_current_user)):
    return templates.TemplateResponse("calendario.html", {"request": request, "current_user": current_user})


@app.get("/allenamenti", response_class=HTMLResponse)
async def list_allenamenti(
        request: Request, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user),
        filter: str = Query("future"), macro_group_id: Optional[int] = Query(None),
        subgroup_id: Optional[int] = Query(None), tipo: Optional[str] = Query(None)
):
    today = date.today()
    query = db.query(models.Allenamento).options(joinedload(models.Allenamento.macro_group),
                                                 joinedload(models.Allenamento.sub_groups))
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
    if macro_group_id:
        query = query.filter(models.Allenamento.macro_group_id == macro_group_id)
    if subgroup_id:
        query = query.join(models.Allenamento.sub_groups).filter(models.SubGroup.id == subgroup_id)
    if tipo:
        query = query.filter(models.Allenamento.tipo == tipo)
    allenamenti = query.all()
    all_groups_obj = db.query(models.MacroGroup).options(joinedload(models.MacroGroup.subgroups)).all()
    all_groups_serializable = [
        {"id": mg.id, "name": mg.name, "subgroups": [{"id": sg.id, "name": sg.name} for sg in mg.subgroups]} for mg in
        all_groups_obj]
    all_types = db.query(models.Allenamento.tipo).distinct().all()
    return templates.TemplateResponse("allenamenti_list.html", {
        "request": request, "allenamenti": allenamenti, "current_user": current_user, "page_title": page_title,
        "all_groups": all_groups_serializable, "all_types": [t[0] for t in all_types],
        "current_filters": {"filter": filter, "macro_group_id": macro_group_id, "subgroup_id": subgroup_id,
                            "tipo": tipo}
    })


@app.get("/turni", response_class=HTMLResponse)
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


@app.get("/rubrica", response_class=HTMLResponse)
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


# ===== Route per le Barche =====
@app.get("/risorse/barche", response_class=HTMLResponse)
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


@app.get("/risorse/barche/nuova", response_class=HTMLResponse)
async def nuova_barca_form(request: Request, db: Session = Depends(get_db),
                           admin_user: models.User = Depends(get_current_admin_user)):
    atleti = db.query(models.User).join(models.User.roles).filter(models.Role.name == 'atleta').order_by(
        models.User.last_name).all()
    return templates.TemplateResponse("crea_barca.html",
                                      {"request": request, "current_user": admin_user, "atleti": atleti})


@app.post("/risorse/barche/nuova", response_class=RedirectResponse)
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


@app.get("/risorse/barche/{barca_id}/modifica", response_class=HTMLResponse)
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


@app.post("/risorse/barche/{barca_id}/modifica", response_class=RedirectResponse)
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


@app.post("/risorse/barche/{barca_id}/elimina", response_class=RedirectResponse)
async def elimina_barca(barca_id: int, db: Session = Depends(get_db),
                        admin_user: models.User = Depends(get_current_admin_user)):
    barca = db.query(models.Barca).filter(models.Barca.id == barca_id).first()
    if not barca: raise HTTPException(status_code=404, detail="Barca non trovata")
    db.delete(barca)
    db.commit()
    return RedirectResponse(url="/risorse/barche", status_code=status.HTTP_303_SEE_OTHER)


# ===== Route per i Pesi =====
@app.get("/risorse/pesi", response_class=HTMLResponse)
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
            if selected_atleta:
                schede = db.query(models.SchedaPesi).filter(models.SchedaPesi.atleta_id == atleta_id).all()
                scheda_data = {s.esercizio_id: s for s in schede}
    elif current_user.is_atleta:
        selected_atleta = current_user
        schede = db.query(models.SchedaPesi).filter(models.SchedaPesi.atleta_id == current_user.id).all()
        scheda_data = {s.esercizio_id: s for s in schede}
    return templates.TemplateResponse("pesi.html",
                                      {"request": request, "current_user": current_user, "esercizi": esercizi,
                                       "atleti": atleti, "selected_atleta": selected_atleta,
                                       "scheda_data": scheda_data})


@app.post("/risorse/pesi/update", response_class=RedirectResponse)
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


@app.post("/risorse/pesi/add_esercizio", response_class=RedirectResponse)
async def add_esercizio_pesi(db: Session = Depends(get_db), admin_user: models.User = Depends(get_current_admin_user),
                             nome: str = Form(...), ordine: int = Form(...)):
    new_esercizio = models.EsercizioPesi(nome=nome, ordine=ordine)
    db.add(new_esercizio)
    db.commit()
    return RedirectResponse(url="/risorse/pesi", status_code=status.HTTP_303_SEE_OTHER)


# ===== API Endpoints =====
@app.get("/api/training/groups")
async def get_training_groups(db: Session = Depends(get_db)):
    macro_groups = db.query(models.MacroGroup).options(joinedload(models.MacroGroup.subgroups)).all()
    return [{"id": mg.id, "name": mg.name, "subgroups": [{"id": sg.id, "name": sg.name} for sg in mg.subgroups]} for mg
            in macro_groups]


@app.get("/api/allenamenti")
async def get_allenamenti_api(db: Session = Depends(get_db), macro_group_id: Optional[int] = None,
                              subgroup_ids: Optional[str] = None):
    query = db.query(models.Allenamento).options(joinedload(models.Allenamento.macro_group),
                                                 joinedload(models.Allenamento.sub_groups))
    if macro_group_id:
        query = query.filter(models.Allenamento.macro_group_id == macro_group_id)
    if subgroup_ids:
        try:
            subgroup_ids_list = [int(id) for id in subgroup_ids.split(',') if id.strip().isdigit()]
            if subgroup_ids_list:
                query = query.join(models.Allenamento.sub_groups).filter(models.SubGroup.id.in_(subgroup_ids_list))
        except (ValueError, TypeError):
            logger.warning(f"Ricevuti subgroup_ids non validi: {subgroup_ids}")
    allenamenti = query.distinct().all()
    formatted_events = []
    for a in allenamenti:
        start_dt, end_dt = parse_orario(a.data, a.orario)
        title = a.tipo
        if a.descrizione: title += f" - {a.descrizione}"
        formatted_events.append({
            "id": a.id, "title": title, "start": start_dt.isoformat(), "end": end_dt.isoformat(),
            "backgroundColor": get_color_for_type(a.tipo), "borderColor": get_color_for_type(a.tipo),
            "extendedProps": {
                "descrizione": a.descrizione, "orario": a.orario, "recurrence_id": a.recurrence_id,
                "macro_group": a.macro_group.name if a.macro_group else "Nessuno",
                "sub_groups": ", ".join([sg.name for sg in a.sub_groups]) if a.sub_groups else "Nessuno",
                "is_recurrent": "Sì" if a.recurrence_id else "No"
            }
        })
    return formatted_events


@app.get("/api/turni")
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


# ===== CRUD Allenamenti =====
@app.get("/allenamenti/nuovo", response_class=HTMLResponse)
async def nuovo_allenamento_form(request: Request, admin_user: models.User = Depends(get_current_admin_user)):
    return templates.TemplateResponse("crea_allenamento.html", {"request": request, "current_user": admin_user})


@app.post("/allenamenti/nuovo", response_class=RedirectResponse)
async def crea_allenamento(
        request: Request, db: Session = Depends(get_db), admin_user: models.User = Depends(get_current_admin_user),
        tipo: str = Form(...), descrizione: Optional[str] = Form(None), data: date = Form(...),
        orario: str = Form(...), orario_personalizzato: Optional[str] = Form(None),
        is_recurring: Optional[str] = Form(None), giorni: Optional[List[str]] = Form(None),
        recurrence_count: Optional[int] = Form(None), macro_group_id: int = Form(...),
        subgroup_ids: List[int] = Form([])
):
    final_orario_str = orario_personalizzato if orario == 'personalizzato' else orario

    if subgroup_ids:
        selected_subgroups = db.query(models.SubGroup).filter(models.SubGroup.id.in_(subgroup_ids)).all()
    else:
        selected_subgroups = db.query(models.SubGroup).filter(models.SubGroup.macro_group_id == macro_group_id).all()

    if is_recurring == 'true':
        if not giorni or not recurrence_count or recurrence_count <= 0:
            return templates.TemplateResponse("crea_allenamento.html", {"request": request,
                                                                        "error_message": "Per la ricorrenza, selezionare i giorni e un numero di occorrenze valido.",
                                                                        "current_user": admin_user}, status_code=400)
        byweekday_dateutil = [DAY_MAP_DATETIL[d] for d in giorni if d in DAY_MAP_DATETIL]
        if not byweekday_dateutil:
            return templates.TemplateResponse("crea_allenamento.html",
                                              {"request": request, "error_message": "Giorni di ricorrenza non validi.",
                                               "current_user": admin_user}, status_code=400)
        start_dt_base, end_dt_base = parse_orario(data, final_orario_str)
        duration = end_dt_base - start_dt_base
        new_recurrence_id = str(uuid.uuid4())
        rule = rrule(WEEKLY, dtstart=start_dt_base, byweekday=byweekday_dateutil, count=recurrence_count)
        occurrences_to_save = []
        for occ_dt in rule:
            new_allenamento = models.Allenamento(
                tipo=tipo, descrizione=descrizione, data=occ_dt.date(),
                orario=f"{occ_dt.strftime('%H:%M')}-{(occ_dt + duration).strftime('%H:%M')}",
                macro_group_id=macro_group_id, recurrence_id=new_recurrence_id
            )
            new_allenamento.sub_groups.extend(selected_subgroups)
            occurrences_to_save.append(new_allenamento)
        db.add_all(occurrences_to_save)
    else:
        nuovo_allenamento = models.Allenamento(tipo=tipo, descrizione=descrizione, data=data, orario=final_orario_str,
                                               macro_group_id=macro_group_id)
        nuovo_allenamento.sub_groups.extend(selected_subgroups)
        db.add(nuovo_allenamento)

    db.commit()
    return RedirectResponse(url="/calendario", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/allenamenti/{id}/modifica", response_class=RedirectResponse)
async def aggiorna_allenamento(
        id: int, db: Session = Depends(get_db), admin_user: models.User = Depends(get_current_admin_user),
        tipo: str = Form(...), descrizione: Optional[str] = Form(None), data: date = Form(...),
        orario: str = Form(...), orario_personalizzato: Optional[str] = Form(None),
        macro_group_id: int = Form(...), subgroup_ids: Optional[List[int]] = Form(None)
):
    allenamento = db.query(models.Allenamento).filter(models.Allenamento.id == id).first()
    if not allenamento: raise HTTPException(status_code=404, detail="Allenamento non trovato")
    allenamento.tipo, allenamento.descrizione, allenamento.data = tipo, descrizione, data
    allenamento.orario = orario_personalizzato if orario == 'personalizzato' else orario
    allenamento.macro_group_id = macro_group_id
    allenamento.sub_groups.clear()
    if subgroup_ids:
        allenamento.sub_groups.extend(db.query(models.SubGroup).filter(models.SubGroup.id.in_(subgroup_ids)).all())
    db.commit()
    return RedirectResponse(url="/calendario", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/allenamenti/delete", response_class=RedirectResponse)
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


@app.post("/turni/assegna", response_class=RedirectResponse)
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


# ===== Route di Autenticazione =====
@app.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login", response_class=RedirectResponse)
async def login(request: Request, db: Session = Depends(get_db), username: str = Form(...), password: str = Form(...)):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user or not security.verify_password(password, user.hashed_password):
        return templates.TemplateResponse("login.html",
                                          {"request": request, "error_message": "Username o password non validi"},
                                          status_code=401)
    request.session["user_id"] = user.id
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/logout", response_class=RedirectResponse)
async def logout(request: Request):
    request.session.pop("user_id", None)
    return RedirectResponse(url="/login?message=Logout effettuato", status_code=status.HTTP_303_SEE_OTHER)


# ===== Sezione Amministrazione Utenti =====

@app.get("/admin/users", response_class=HTMLResponse)
async def admin_users_list(
        request: Request, db: Session = Depends(get_db), admin_user: models.User = Depends(get_current_admin_user),
        role_ids: List[int] = Query([]), categories: List[str] = Query([]),
        enrollment_year: Optional[int] = Query(None), cert_expiring: bool = Query(False),
        sort_by: str = Query("last_name"), sort_dir: str = Query("asc")
):
    query = db.query(models.User).options(joinedload(models.User.roles))
    if role_ids:
        query = query.join(models.user_roles).filter(models.user_roles.c.role_id.in_(role_ids))
    if enrollment_year:
        query = query.filter(models.User.enrollment_year == enrollment_year)
    if cert_expiring:
        two_months_from_now = date.today() + timedelta(days=60)
        query = query.filter(models.User.certificate_expiration <= two_months_from_now)

    users = query.all()
    if categories:
        users = [user for user in users if user.category in categories]

    reverse = sort_dir == "desc"
    if sort_by == "name":
        users.sort(key=lambda u: f"{u.first_name} {u.last_name}", reverse=reverse)
    elif sort_by == "username":
        users.sort(key=lambda u: u.username, reverse=reverse)
    elif sort_by == "category":
        users.sort(key=lambda u: u.category, reverse=reverse)
    elif sort_by == "date_of_birth":
        users.sort(key=lambda u: u.date_of_birth or date.min, reverse=reverse)
    else:
        users.sort(key=lambda u: u.last_name, reverse=reverse)

    all_roles = db.query(models.Role).all()
    all_years = sorted([y[0] for y in db.query(models.User.enrollment_year).distinct().all() if y[0] is not None],
                       reverse=True)
    all_categories = sorted(list(set(u.category for u in db.query(models.User).all() if u.category != "N/D")))

    return templates.TemplateResponse("admin_users_list.html", {
        "request": request, "users": users, "current_user": admin_user,
        "all_roles": all_roles, "all_categories": all_categories, "all_years": all_years,
        "current_filters": {"role_ids": role_ids, "categories": categories, "enrollment_year": enrollment_year,
                            "cert_expiring": cert_expiring},
        "sort_by": sort_by, "sort_dir": sort_dir
    })


@app.get("/admin/users/add", response_class=HTMLResponse)
async def admin_add_user_form(request: Request, db: Session = Depends(get_db),
                              admin_user: models.User = Depends(get_current_admin_user)):
    roles = db.query(models.Role).order_by(models.Role.name).all()
    return templates.TemplateResponse("admin_user_add.html",
                                      {"request": request, "current_user": admin_user, "all_roles": roles, "user": {},
                                       "user_role_ids": set()})


@app.post("/admin/users/add", response_class=RedirectResponse)
async def admin_add_user(db: Session = Depends(get_db), admin_user: models.User = Depends(get_current_admin_user),
                         username: str = Form(...), password: str = Form(...), first_name: str = Form(...),
                         last_name: str = Form(...),
                         email: str = Form(...), date_of_birth: date = Form(...), roles_ids: List[int] = Form(...),
                         phone_number: Optional[str] = Form(None), tax_code: Optional[str] = Form(None),
                         enrollment_year: Optional[int] = Form(None), membership_date: Optional[date] = Form(None),
                         certificate_expiration: Optional[date] = Form(None), address: Optional[str] = Form(None),
                         manual_category: Optional[str] = Form(None)
                         ):
    if db.query(models.User).filter(or_(models.User.username == username, models.User.email == email)).first():
        return RedirectResponse(url="/admin/users/add?error=Username o email già in uso",
                                status_code=status.HTTP_303_SEE_OTHER)
    selected_roles = db.query(models.Role).filter(models.Role.id.in_(roles_ids)).all()
    new_user = models.User(
        username=username, hashed_password=security.get_password_hash(password),
        first_name=first_name, last_name=last_name, email=email, date_of_birth=date_of_birth,
        phone_number=phone_number, tax_code=tax_code, enrollment_year=enrollment_year,
        membership_date=membership_date, certificate_expiration=certificate_expiration,
        address=address, manual_category=manual_category if manual_category else None,
        roles=selected_roles
    )
    db.add(new_user)
    db.commit()
    return RedirectResponse(url="/admin/users?message=Utente creato con successo",
                            status_code=status.HTTP_303_SEE_OTHER)


@app.get("/admin/users/{user_id}", response_class=HTMLResponse)
async def admin_view_user(user_id: int, request: Request, db: Session = Depends(get_db),
                          admin_user: models.User = Depends(get_current_admin_user)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user: raise HTTPException(status_code=404, detail="Utente non trovato")
    return templates.TemplateResponse("admin_user_detail.html",
                                      {"request": request, "user": user, "current_user": admin_user})


@app.get("/admin/users/{user_id}/edit", response_class=HTMLResponse)
async def admin_edit_user_form(user_id: int, request: Request, db: Session = Depends(get_db),
                               admin_user: models.User = Depends(get_current_admin_user)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user: raise HTTPException(status_code=404, detail="Utente non trovato")
    roles = db.query(models.Role).all()
    user_role_ids = {role.id for role in user.roles}
    return templates.TemplateResponse("admin_user_edit.html",
                                      {"request": request, "user": user, "current_user": admin_user, "all_roles": roles,
                                       "user_role_ids": user_role_ids})


@app.post("/admin/users/{user_id}/edit", response_class=RedirectResponse)
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


@app.post("/admin/users/{user_id}/delete", response_class=RedirectResponse)
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
