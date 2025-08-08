# File: routers/trainings.py
import uuid
from datetime import date, datetime, time, timedelta
from typing import List, Optional
from fastapi import APIRouter, Request, Depends, Form, Query, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session, joinedload
from dateutil.rrule import rrule, WEEKLY
from fastapi.templating import Jinja2Templates
import models
from database import get_db
from dependencies import get_current_user, get_current_admin_user
from utils import DAY_MAP_DATETIL, parse_orario, get_color_for_type

router = APIRouter(tags=["Allenamenti e Calendario"])
templates = Jinja2Templates(directory="templates")


def _list_categories(db: Session) -> List[str]:
    """Return all available category names ordered by configured priority."""
    return [c.nome for c in db.query(models.Categoria).order_by(models.Categoria.ordine).all()]


@router.get("/calendario", response_class=HTMLResponse)
async def view_calendar(request: Request, current_user: models.User = Depends(get_current_user)):
    return templates.TemplateResponse("allenamenti/calendario.html", {"request": request, "current_user": current_user})

@router.get("/allenamenti", response_class=HTMLResponse)
async def list_allenamenti(
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    filter: str = Query("future"),
    macro_group_id: Optional[str] = Query(None),
    subgroup_id: Optional[str] = Query(None),
    tipo: Optional[str] = Query(None),
):
    today = date.today()
    query = db.query(models.Allenamento).options(
        joinedload(models.Allenamento.macro_group),
        joinedload(models.Allenamento.sub_groups),
    )
    mg_id = int(macro_group_id) if macro_group_id else None
    sg_id = int(subgroup_id) if subgroup_id else None
    if filter == "future":
        page_title, query = "Prossimi Allenamenti", query.filter(models.Allenamento.data >= today).order_by(models.Allenamento.data.asc(), models.Allenamento.orario.asc())
    elif filter == "past":
        page_title, query = "Allenamenti Passati", query.filter(models.Allenamento.data < today).order_by(models.Allenamento.data.desc(), models.Allenamento.orario.desc())
    else:
        page_title, query = "Tutti gli Allenamenti", query.order_by(models.Allenamento.data.desc())
    if current_user.is_atleta and not (current_user.is_admin or current_user.is_allenatore):
        query = query.join(models.Allenamento.sub_groups).filter(
            models.SubGroup.name == current_user.category
        )
    elif mg_id or sg_id:
        query = query.join(models.Allenamento.sub_groups)
        if mg_id:
            query = query.filter(models.SubGroup.macro_group_id == mg_id)
        if sg_id:
            query = query.filter(models.SubGroup.id == sg_id)
    if tipo:
        query = query.filter(models.Allenamento.tipo == tipo)
    all_groups_obj = db.query(models.MacroGroup).options(joinedload(models.MacroGroup.subgroups)).all()
    all_groups = [{"id": mg.id, "name": mg.name, "subgroups": [{"id": sg.id, "name": sg.name} for sg in mg.subgroups]} for mg in all_groups_obj]
    all_types = [t[0] for t in db.query(models.Allenamento.tipo).distinct().all()]
    return templates.TemplateResponse(
        "allenamenti/allenamenti_list.html",
        {
            "request": request,
            "allenamenti": query.all(),
            "current_user": current_user,
            "page_title": page_title,
            "all_groups": all_groups,
            "all_types": all_types,
            "current_filters": {
                "filter": filter,
                "macro_group_id": mg_id,
                "subgroup_id": sg_id,
                "tipo": tipo,
            },
        },
    )

@router.get("/allenamenti/nuovo", response_class=HTMLResponse)
async def nuovo_allenamento_form(
    request: Request,
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(get_current_admin_user),
):
    categories = _list_categories(db)
    return templates.TemplateResponse(
        "allenamenti/crea_allenamento.html",
        {"request": request, "current_user": admin_user, "categories": categories, "selected_category_names": []},
    )

@router.post("/allenamenti/nuovo", response_class=RedirectResponse)
async def crea_allenamento(
    request: Request,
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(get_current_admin_user),
    tipo: str = Form(...),
    descrizione: Optional[str] = Form(None),
    data: date = Form(...),
    orario: str = Form(...),
    orario_personalizzato: Optional[str] = Form(None),
    is_recurring: Optional[str] = Form(None),
    giorni: Optional[List[str]] = Form(None),
    recurrence_count: Optional[int] = Form(None),
    category_names: List[str] = Form([]),
):
    final_orario = orario_personalizzato if orario == "personalizzato" else orario
    subgroups = db.query(models.SubGroup).filter(models.SubGroup.name.in_(category_names)).all() if category_names else []
    if not subgroups or len(subgroups) != len(category_names):
        categories = _list_categories(db)
        return templates.TemplateResponse(
            "allenamenti/crea_allenamento.html",
            {
                "request": request,
                "current_user": admin_user,
                "categories": categories,
                "selected_category_names": category_names,
                "error_message": "Seleziona almeno una categoria valida.",
            },
            status_code=400,
        )
    macro_ids = {sg.macro_group_id for sg in subgroups if sg.macro_group_id}
    macro_group_id = next(iter(macro_ids)) if len(macro_ids) == 1 else None
    if is_recurring == "true":
        if not giorni or not recurrence_count or recurrence_count <= 0:
            categories = _list_categories(db)
            return templates.TemplateResponse(
                "allenamenti/crea_allenamento.html",
                {
                    "request": request,
                    "current_user": admin_user,
                    "categories": categories,
                    "selected_category_names": category_names,
                    "error_message": "Per la ricorrenza, selezionare i giorni e un numero di occorrenze valido.",
                },
                status_code=400,
            )
        byweekday = [DAY_MAP_DATETIL[d] for d in giorni if d in DAY_MAP_DATETIL]
        start_dt, end_dt = parse_orario(data, final_orario)
        duration = end_dt - start_dt
        rec_id = str(uuid.uuid4())
        rule = rrule(WEEKLY, dtstart=start_dt, byweekday=byweekday, count=recurrence_count)
        for occ_dt in rule:
            new_a = models.Allenamento(
                tipo=tipo,
                descrizione=descrizione,
                data=occ_dt.date(),
                orario=f"{occ_dt.strftime('%H:%M')}-{(occ_dt + duration).strftime('%H:%M')}",
                macro_group_id=macro_group_id,
                recurrence_id=rec_id,
            )
            new_a.sub_groups.extend(subgroups)
            db.add(new_a)
    else:
        new_a = models.Allenamento(
            tipo=tipo,
            descrizione=descrizione,
            data=data,
            orario=final_orario,
            macro_group_id=macro_group_id,
        )
        new_a.sub_groups.extend(subgroups)
        db.add(new_a)
    db.commit()
    return RedirectResponse(url="/calendario", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/allenamenti/{id}/modifica", response_class=HTMLResponse)
async def modifica_allenamento_form(
    id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(get_current_admin_user),
):
    allenamento = db.query(models.Allenamento).options(joinedload(models.Allenamento.sub_groups)).get(id)
    if not allenamento:
        raise HTTPException(status_code=404, detail="Allenamento non trovato")
    categories = _list_categories(db)
    selected_category_names = [sg.name for sg in allenamento.sub_groups]
    return templates.TemplateResponse(
        "allenamenti/modifica_allenamento.html",
        {
            "request": request,
            "current_user": admin_user,
            "allenamento": allenamento,
            "categories": categories,
            "selected_category_names": selected_category_names,
        },
    )

@router.post("/allenamenti/{id}/modifica", response_class=RedirectResponse)
async def aggiorna_allenamento(
    id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(get_current_admin_user),
    tipo: str = Form(...),
    descrizione: Optional[str] = Form(None),
    data: date = Form(...),
    orario: str = Form(...),
    orario_personalizzato: Optional[str] = Form(None),
    category_names: List[str] = Form([]),
):
    allenamento = db.query(models.Allenamento).get(id)
    if not allenamento:
        raise HTTPException(status_code=404, detail="Allenamento non trovato")
    subgroups = db.query(models.SubGroup).filter(models.SubGroup.name.in_(category_names)).all() if category_names else []
    if not subgroups or len(subgroups) != len(category_names):
        categories = _list_categories(db)
        return templates.TemplateResponse(
            "allenamenti/modifica_allenamento.html",
            {
                "request": request,
                "current_user": admin_user,
                "allenamento": allenamento,
                "categories": categories,
                "selected_category_names": category_names,
                "error_message": "Seleziona almeno una categoria valida.",
            },
            status_code=400,
        )
    macro_ids = {sg.macro_group_id for sg in subgroups if sg.macro_group_id}
    macro_group_id = next(iter(macro_ids)) if len(macro_ids) == 1 else None
    allenamento.tipo = tipo
    allenamento.descrizione = descrizione
    allenamento.data = data
    allenamento.macro_group_id = macro_group_id
    allenamento.orario = orario_personalizzato if orario == "personalizzato" else orario
    allenamento.sub_groups = subgroups
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
    return [
        {
            "id": mg.id,
            "name": mg.name,
            "subgroups": [{"id": sg.id, "name": sg.name} for sg in mg.subgroups],
        }
        for mg in macro_groups
    ]


@router.get("/api/training/types")
async def get_training_types(db: Session = Depends(get_db)):
    return [t[0] for t in db.query(models.Allenamento.tipo).distinct().order_by(models.Allenamento.tipo)]


@router.get("/api/all-categories")
def list_all_categories(db: Session = Depends(get_db)):
    return [
        {"id": c.id, "name": c.nome}
        for c in db.query(models.Categoria).order_by(models.Categoria.ordine)
    ]


@router.get("/api/allenamenti")
async def get_allenamenti_api(
    db: Session = Depends(get_db),
    macro_group_ids: List[int] = Query([]),
    type_filter: List[str] = Query([]),
    category_filter: List[str] = Query([]),
    user_category: Optional[str] = None,
):
    query = db.query(models.Allenamento).options(
        joinedload(models.Allenamento.macro_group),
        joinedload(models.Allenamento.sub_groups),
    )

    if macro_group_ids or user_category or category_filter:
        query = query.join(models.Allenamento.sub_groups)
    if macro_group_ids:
        query = query.filter(models.SubGroup.macro_group_id.in_(macro_group_ids))
    if category_filter:
        query = query.filter(models.SubGroup.name.in_(category_filter))
    if user_category:
        query = query.filter(models.SubGroup.name == user_category)
    if type_filter:
        query = query.filter(models.Allenamento.tipo.in_(type_filter))

    events = []
    for a in query.distinct().all():
        start_dt, end_dt = parse_orario(a.data, a.orario)
        macro_name = (
            a.macro_group.name
            if a.macro_group
            else ", ".join(
                sorted({sg.macro_group.name for sg in a.sub_groups if sg.macro_group})
            )
            or "Nessuno"
        )
        categories = ", ".join([sg.name for sg in a.sub_groups]) or "Nessuno"
        events.append(
            {
                "id": a.id,
                "title": f"{a.tipo} - {a.descrizione}" if a.descrizione else a.tipo,
                "start": start_dt.isoformat(),
                "end": end_dt.isoformat(),
                "backgroundColor": get_color_for_type(a.tipo),
                "borderColor": get_color_for_type(a.tipo),
                "extendedProps": {
                    "descrizione": a.descrizione,
                    "orario": a.orario,
                    "recurrence_id": a.recurrence_id,
                    "macro_group": macro_name,
                    "categories": categories,
                    "is_recurrent": "Sì" if a.recurrence_id else "No",
                },
            }
        )
    return events


@router.get("/api/turni")
async def get_turni_api(db: Session = Depends(get_db)):
    events = []
    for t in db.query(models.Turno).options(joinedload(models.Turno.user)).all():
        start_hour, end_hour = (8, 12) if t.fascia_oraria == "Mattina" else (17, 21)
        start_dt = datetime.combine(t.data, time(hour=start_hour))
        end_dt = datetime.combine(t.data, time(hour=end_hour))
        events.append(
            {
                "id": t.id,
                "title": f"{t.user.first_name} {t.user.last_name}" if t.user else "Turno Libero",
                "start": start_dt.isoformat(),
                "end": end_dt.isoformat(),
                "backgroundColor": "#198754" if t.user else "#dc3545",
                "borderColor": "#198754" if t.user else "#dc3545",
                "extendedProps": {"user_id": t.user_id, "fascia_oraria": t.fascia_oraria},
            }
        )
    return events
