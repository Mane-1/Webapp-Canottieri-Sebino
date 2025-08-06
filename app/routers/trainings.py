# File: routers/trainings.py
import uuid
from datetime import date, datetime, time, timedelta
from typing import List, Optional
from fastapi import APIRouter, Request, Depends, Form, Query, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session, joinedload
from dateutil.rrule import rrule, WEEKLY
from fastapi.templating import Jinja2Templates
from app.dependencies.dependencies import templates
from app.database.database import get_db
from app import models
from app.security import security
from app.database.database import get_db
from app.dependencies.dependencies import get_current_user, get_current_admin_user
from app.utils.utils import DAY_MAP_DATETIL, parse_orario, get_color_for_type

from app.dependencies.dependencies import templates, get_current_user, get_db

@router.get("/dashboard")
async def dashboard(request: Request, db: Session = Depends(get_db),
                    current_user: models.User = Depends(get_current_user)):
    return templates.TemplateResponse("dashboard.html", {"request": request, ...})

router = APIRouter(tags=["Allenamenti e Calendario"])
templates = Jinja2Templates(directory="templates")

@router.get("/calendario", response_class=HTMLResponse)
async def view_calendar(request: Request, current_user: models.User = Depends(get_current_user)):
    return templates.TemplateResponse("allenamenti/calendario.html", {"request": request, "current_user": current_user})

@router.get("/allenamenti", response_class=HTMLResponse)
async def list_allenamenti(request: Request, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user), filter: str = Query("future"), macro_group_id: Optional[int] = Query(None), subgroup_id: Optional[int] = Query(None), tipo: Optional[str] = Query(None)):
    today = date.today()
    query = db.query(models.Allenamento).options(joinedload(models.Allenamento.macro_group), joinedload(models.Allenamento.sub_groups))
    if filter == "future": page_title, query = "Prossimi Allenamenti", query.filter(models.Allenamento.data >= today).order_by(models.Allenamento.data.asc(), models.Allenamento.orario.asc())
    elif filter == "past": page_title, query = "Allenamenti Passati", query.filter(models.Allenamento.data < today).order_by(models.Allenamento.data.desc(), models.Allenamento.orario.desc())
    else: page_title, query = "Tutti gli Allenamenti", query.order_by(models.Allenamento.data.desc())
    if macro_group_id: query = query.filter(models.Allenamento.macro_group_id == macro_group_id)
    if subgroup_id: query = query.join(models.Allenamento.sub_groups).filter(models.SubGroup.id == subgroup_id)
    if tipo: query = query.filter(models.Allenamento.tipo == tipo)
    all_groups_obj = db.query(models.MacroGroup).options(joinedload(models.MacroGroup.subgroups)).all()
    all_groups = [{"id": mg.id, "name": mg.name, "subgroups": [{"id": sg.id, "name": sg.name} for sg in mg.subgroups]} for mg in all_groups_obj]
    all_types = [t[0] for t in db.query(models.Allenamento.tipo).distinct().all()]
    return templates.TemplateResponse("allenamenti/allenamenti_list.html", {"request": request, "allenamenti": query.all(), "current_user": current_user, "page_title": page_title, "all_groups": all_groups, "all_types": all_types, "current_filters": {"filter": filter, "macro_group_id": macro_group_id, "subgroup_id": subgroup_id, "tipo": tipo}})

@router.get("/allenamenti/nuovo", response_class=HTMLResponse)
async def nuovo_allenamento_form(request: Request, admin_user: models.User = Depends(get_current_admin_user)):
    return templates.TemplateResponse("allenamenti/crea_allenamento.html", {"request": request, "current_user": admin_user})

@router.post("/allenamenti/nuovo", response_class=RedirectResponse)
async def crea_allenamento(request: Request, db: Session = Depends(get_db), admin_user: models.User = Depends(get_current_admin_user), tipo: str = Form(...), descrizione: Optional[str] = Form(None), data: date = Form(...), orario: str = Form(...), orario_personalizzato: Optional[str] = Form(None), is_recurring: Optional[str] = Form(None), giorni: Optional[List[str]] = Form(None), recurrence_count: Optional[int] = Form(None), macro_group_id: int = Form(...), subgroup_ids: List[int] = Form([])):
    final_orario = orario_personalizzato if orario == 'personalizzato' else orario
    subgroups = db.query(models.SubGroup).filter(models.SubGroup.id.in_(subgroup_ids)).all() if subgroup_ids else db.query(models.SubGroup).filter_by(macro_group_id=macro_group_id).all()
    if is_recurring == 'true':
        if not giorni or not recurrence_count or recurrence_count <= 0: return templates.TemplateResponse("allenamenti/crea_allenamento.html", {"request": request, "error_message": "Per la ricorrenza, selezionare i giorni e un numero di occorrenze valido.", "current_user": admin_user}, status_code=400)
        byweekday = [DAY_MAP_DATETIL[d] for d in giorni if d in DAY_MAP_DATETIL]
        start_dt, end_dt = parse_orario(data, final_orario)
        duration = end_dt - start_dt
        rec_id = str(uuid.uuid4())
        rule = rrule(WEEKLY, dtstart=start_dt, byweekday=byweekday, count=recurrence_count)
        for occ_dt in rule:
            new_a = models.Allenamento(tipo=tipo, descrizione=descrizione, data=occ_dt.date(), orario=f"{occ_dt.strftime('%H:%M')}-{(occ_dt + duration).strftime('%H:%M')}", macro_group_id=macro_group_id, recurrence_id=rec_id)
            new_a.sub_groups.extend(subgroups)
            db.add(new_a)
    else:
        new_a = models.Allenamento(tipo=tipo, descrizione=descrizione, data=data, orario=final_orario, macro_group_id=macro_group_id)
        new_a.sub_groups.extend(subgroups)
        db.add(new_a)
    db.commit()
    return RedirectResponse(url="/calendario", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/allenamenti/{id}/modifica", response_class=HTMLResponse)
async def modifica_allenamento_form(id: int, request: Request, db: Session = Depends(get_db), admin_user: models.User = Depends(get_current_admin_user)):
    allenamento = db.query(models.Allenamento).options(joinedload(models.Allenamento.sub_groups)).get(id)
    if not allenamento: raise HTTPException(status_code=404, detail="Allenamento non trovato")
    selected_subgroup_ids = [sg.id for sg in allenamento.sub_groups]
    return templates.TemplateResponse("allenamenti/modifica_allenamento.html", {"request": request, "current_user": admin_user, "allenamento": allenamento, "selected_subgroup_ids": selected_subgroup_ids})

@router.post("/allenamenti/{id}/modifica", response_class=RedirectResponse)
async def aggiorna_allenamento(id: int, db: Session = Depends(get_db), admin_user: models.User = Depends(get_current_admin_user), tipo: str = Form(...), descrizione: Optional[str] = Form(None), data: date = Form(...), orario: str = Form(...), orario_personalizzato: Optional[str] = Form(None), macro_group_id: int = Form(...), subgroup_ids: List[int] = Form([])):
    allenamento = db.query(models.Allenamento).get(id)
    if not allenamento: raise HTTPException(status_code=404, detail="Allenamento non trovato")
    allenamento.tipo, allenamento.descrizione, allenamento.data, allenamento.macro_group_id = tipo, descrizione, data, macro_group_id
    allenamento.orario = orario_personalizzato if orario == 'personalizzato' else orario
    allenamento.sub_groups = db.query(models.SubGroup).filter(models.SubGroup.id.in_(subgroup_ids)).all()
    db.commit()
    return RedirectResponse(url="/calendario", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/allenamenti/delete", response_class=RedirectResponse)
async def delete_allenamento_events(db: Session = Depends(get_db), admin_user: models.User = Depends(get_current_admin_user), allenamento_id: int = Form(...), deletion_type: str = Form(...)):
    a = db.query(models.Allenamento).get(allenamento_id)
    if not a: raise HTTPException(status_code=404, detail="Allenamento non trovato")
    if deletion_type == 'future' and a.recurrence_id:
        db.query(models.Allenamento).filter(models.Allenamento.recurrence_id == a.recurrence_id, models.Allenamento.data >= a.data).delete(synchronize_session=False)
    else: db.delete(a)
    db.commit()
    return RedirectResponse(url="/calendario", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/turni", response_class=HTMLResponse)
async def view_turni(request: Request, db: Session = Depends(get_db), admin_user: models.User = Depends(get_current_admin_user), week_offset: int = 0):
    today = date.today() + timedelta(weeks=week_offset)
    start_of_week, end_of_week = today - timedelta(days=today.weekday()), today - timedelta(days=today.weekday()) + timedelta(days=6)
    allenatori = db.query(models.User).join(models.User.roles).filter(models.Role.name == 'allenatore').all()
    turni = db.query(models.Turno).filter(models.Turno.data.between(start_of_week, end_of_week)).order_by(models.Turno.data, models.Turno.fascia_oraria).all()
    return templates.TemplateResponse("turni.html", {"request": request, "current_user": admin_user, "allenatori": allenatori, "turni": turni, "week_offset": week_offset, "week_start": start_of_week, "week_end": end_of_week})

@router.post("/turni/assegna", response_class=RedirectResponse)
async def assegna_turno(db: Session = Depends(get_db), admin_user: models.User = Depends(get_current_admin_user), turno_id: int = Form(...), user_id: int = Form(...), week_offset: int = Form(0)):
    turno = db.query(models.Turno).get(turno_id)
    if not turno: raise HTTPException(status_code=404, detail="Turno non trovato")
    if user_id == 0: turno.user_id = None
    else:
        user = db.query(models.User).get(user_id)
        if not user or not user.is_allenatore: raise HTTPException(status_code=400, detail="Utente non valido o non è un allenatore")
        turno.user_id = user_id
    db.commit()
    return RedirectResponse(url=f"/turni?week_offset={week_offset}", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/api/training/groups")
async def get_training_groups(db: Session = Depends(get_db)):
    macro_groups = db.query(models.MacroGroup).options(joinedload(models.MacroGroup.subgroups)).all()
    return [{"id": mg.id, "name": mg.name, "subgroups": [{"id": sg.id, "name": sg.name} for sg in mg.subgroups]} for mg in macro_groups]

@router.get("/api/allenamenti")
async def get_allenamenti_api(db: Session = Depends(get_db), macro_group_id: Optional[int] = None, subgroup_ids: Optional[str] = None):
    query = db.query(models.Allenamento).options(joinedload(models.Allenamento.macro_group), joinedload(models.Allenamento.sub_groups))
    if macro_group_id: query = query.filter(models.Allenamento.macro_group_id == macro_group_id)
    if subgroup_ids:
        ids = [int(id) for id in subgroup_ids.split(',') if id.strip().isdigit()]
        if ids: query = query.join(models.Allenamento.sub_groups).filter(models.SubGroup.id.in_(ids))
    events = []
    for a in query.distinct().all():
        start_dt, end_dt = parse_orario(a.data, a.orario)
        events.append({"id": a.id, "title": f"{a.tipo} - {a.descrizione}" if a.descrizione else a.tipo, "start": start_dt.isoformat(), "end": end_dt.isoformat(), "backgroundColor": get_color_for_type(a.tipo), "borderColor": get_color_for_type(a.tipo), "extendedProps": {"descrizione": a.descrizione, "orario": a.orario, "recurrence_id": a.recurrence_id, "macro_group": a.macro_group.name if a.macro_group else "Nessuno", "sub_groups": ", ".join([sg.name for sg in a.sub_groups]) or "Nessuno", "is_recurrent": "Sì" if a.recurrence_id else "No"}})
    return events

@router.get("/api/turni")
async def get_turni_api(db: Session = Depends(get_db)):
    events = []
    for t in db.query(models.Turno).options(joinedload(models.Turno.user)).all():
        start_hour, end_hour = (8, 12) if t.fascia_oraria == "Mattina" else (17, 21)
        start_dt, end_dt = datetime.combine(t.data, time(hour=start_hour)), datetime.combine(t.data, time(hour=end_hour))
        events.append({"id": t.id, "title": f"{t.user.first_name} {t.user.last_name}" if t.user else "Turno Libero", "start": start_dt.isoformat(), "end": end_dt.isoformat(), "backgroundColor": "#198754" if t.user else "#dc3545", "borderColor": "#198754" if t.user else "#dc3545", "extendedProps": {"user_id": t.user_id, "fascia_oraria": t.fascia_oraria}})
    return events