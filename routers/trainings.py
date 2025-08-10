# File: routers/trainings.py
import uuid
from datetime import date, datetime, time, timedelta
from typing import Dict, List, Optional
from fastapi import APIRouter, Request, Depends, Form, Query, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session, joinedload
from dateutil.rrule import rrule, WEEKLY
from fastapi.templating import Jinja2Templates
import models
from database import get_db
from dependencies import (
    get_current_user,
    get_current_admin_user,
    get_current_admin_or_coach_user,
)
from utils import DAY_MAP_DATETIL, parse_orario, get_color_for_type

CATEGORY_GROUPS: Dict[str, List[str]] = {
    "Over14": ["Ragazzo", "Junior", "Under 23", "Senior"],
    "Master": ["Master"],
    "Under14": ["Allievo A", "Allievo B1", "Allievo B2", "Allievo C", "Cadetto"],
}

router = APIRouter(tags=["Allenamenti e Calendario"])
templates = Jinja2Templates(directory="templates")
templates.env.globals['get_color_for_type'] = get_color_for_type


def _group_categories(db: Session) -> Dict[str, List[str]]:
    """Return category names grouped for visual sections."""
    groups: Dict[str, List[str]] = {k: [] for k in CATEGORY_GROUPS.keys()}
    categorie = db.query(models.Categoria).order_by(models.Categoria.ordine).all()
    for cat in categorie:
        for group, names in CATEGORY_GROUPS.items():
            if cat.nome in names:
                groups[group].append(cat.nome)
                break
    return groups


@router.get("/calendario", response_class=HTMLResponse)
async def view_calendar(
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    all_categories = [c.nome for c in db.query(models.Categoria).order_by(models.Categoria.nome)]
    all_types = [t[0] for t in db.query(models.Allenamento.tipo).distinct().order_by(models.Allenamento.tipo)]
    all_coaches = (
        db.query(models.User)
        .join(models.User.roles)
        .filter(models.Role.name == "allenatore")
        .order_by(models.User.first_name, models.User.last_name)
        .all()
    )
    return templates.TemplateResponse(
        "allenamenti/calendario.html",
        {
            "request": request,
            "current_user": current_user,
            "all_categories": all_categories,
            "all_types": all_types,
            "all_coaches": all_coaches,
        },
    )

@router.get("/allenamenti", response_class=HTMLResponse, name="list_allenamenti")
async def list_allenamenti(
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    filter: str = Query("future"),
    category: Optional[str] = Query(None),
    tipo: Optional[str] = Query(None),
    coach_id: Optional[int] = Query(None),
    unassigned: bool = Query(False),
):
    today = date.today()
    query = db.query(models.Allenamento).options(
        joinedload(models.Allenamento.categories),
        joinedload(models.Allenamento.coaches),
    )
    if filter == "future":
        page_title, query = "Prossimi Allenamenti", query.filter(models.Allenamento.data >= today).order_by(models.Allenamento.data.asc(), models.Allenamento.orario.asc())
    elif filter == "past":
        page_title, query = "Allenamenti Passati", query.filter(models.Allenamento.data < today).order_by(models.Allenamento.data.desc(), models.Allenamento.orario.desc())
    else:
        page_title, query = "Tutti gli Allenamenti", query.order_by(models.Allenamento.data.desc())
    if current_user.is_atleta and not (current_user.is_admin or current_user.is_allenatore):
        query = query.join(models.Allenamento.categories).filter(
            models.Categoria.nome == current_user.category
        )
    elif category:
        query = query.join(models.Allenamento.categories).filter(
            models.Categoria.nome == category
        )
    if tipo:
        query = query.filter(models.Allenamento.tipo == tipo)
    if coach_id:
        query = query.join(models.Allenamento.coaches).filter(models.User.id == coach_id)
    elif unassigned:
        query = query.outerjoin(models.Allenamento.coaches).filter(models.User.id == None)
    all_categories = [c.nome for c in db.query(models.Categoria).order_by(models.Categoria.nome).all()]
    all_types = [t[0] for t in db.query(models.Allenamento.tipo).distinct().all()]
    all_coaches = (
        db.query(models.User)
        .join(models.User.roles)
        .filter(models.Role.name == "allenatore")
        .order_by(models.User.first_name, models.User.last_name)
        .all()
    )
    return templates.TemplateResponse(
        "allenamenti/allenamenti_list.html",
        {
            "request": request,
            "allenamenti": query.all(),
            "current_user": current_user,
            "page_title": page_title,
            "all_categories": all_categories,
            "all_types": all_types,
            "all_coaches": all_coaches,
            "current_filters": {
                "filter": filter,
                "category": category,
                "tipo": tipo,
                "coach_id": coach_id,
                "unassigned": unassigned,
            },
        },
    )

@router.get("/allenamenti/nuovo", response_class=HTMLResponse)
async def nuovo_allenamento_form(
    request: Request,
    db: Session = Depends(get_db),
    staff_user: models.User = Depends(get_current_admin_or_coach_user),
):
    grouped_categories = _group_categories(db)
    available_coaches = (
        db.query(models.User)
        .join(models.User.roles)
        .filter(models.Role.name == "allenatore")
        .order_by(models.User.first_name, models.User.last_name)
        .all()
    )
    return templates.TemplateResponse(
        "allenamenti/crea_allenamento.html",
        {
            "request": request,
            "current_user": staff_user,
            "grouped_categories": grouped_categories,
            "selected_category_names": [],
            "available_coaches": available_coaches,
            "selected_coach_ids": [],
        },
    )

@router.post("/allenamenti/nuovo", response_class=RedirectResponse)
async def crea_allenamento(
    request: Request,
    db: Session = Depends(get_db),
    staff_user: models.User = Depends(get_current_admin_or_coach_user),
    tipo: str = Form(...),
    descrizione: Optional[str] = Form(None),
    data: date = Form(...),
    orario: str = Form(...),
    orario_start: Optional[str] = Form(None),
    orario_end: Optional[str] = Form(None),
    is_recurring: Optional[str] = Form(None),
    giorni: Optional[List[str]] = Form(None),
    recurrence_count: Optional[int] = Form(None),
    recurrence_end_date: Optional[date] = Form(None),
    coach_ids: List[int] = Form([]),
    category_names: List[str] = Form([]),
):
    if orario == "personalizzato":
        if not orario_start or not orario_end:
            grouped_categories = _group_categories(db)
            available_coaches = (
                db.query(models.User)
                .join(models.User.roles)
                .filter(models.Role.name == "allenatore")
                .order_by(models.User.first_name, models.User.last_name)
                .all()
            )
            return templates.TemplateResponse(
                "allenamenti/crea_allenamento.html",
                {
                    "request": request,
                    "current_user": staff_user,
                    "grouped_categories": grouped_categories,
                    "selected_category_names": category_names,
                    "available_coaches": available_coaches,
                    "selected_coach_ids": coach_ids,
                    "error_message": "Specifica un orario di inizio e fine valido.",
                },
                status_code=400,
            )
        final_orario = f"{orario_start}-{orario_end}"
    else:
        final_orario = orario
    categories = (
        db.query(models.Categoria).filter(models.Categoria.nome.in_(category_names)).all()
        if category_names
        else []
    )
    if not categories or len(categories) != len(category_names):
        grouped_categories = _group_categories(db)
        return templates.TemplateResponse(
            "allenamenti/crea_allenamento.html",
            {
                "request": request,
                "current_user": staff_user,
                "grouped_categories": grouped_categories,
                "selected_category_names": category_names,
                "error_message": "Seleziona almeno una categoria valida.",
            },
            status_code=400,
        )
    coaches = []
    if coach_ids:
        coaches = (
            db.query(models.User)
            .join(models.User.roles)
            .filter(models.Role.name == "allenatore", models.User.id.in_(coach_ids))
            .all()
        )
        if len(coaches) != len(coach_ids) or len(coach_ids) > 3:
            grouped_categories = _group_categories(db)
            available_coaches = (
                db.query(models.User)
                .join(models.User.roles)
                .filter(models.Role.name == "allenatore")
                .order_by(models.User.first_name, models.User.last_name)
                .all()
            )
            return templates.TemplateResponse(
                "allenamenti/crea_allenamento.html",
                {
                    "request": request,
                    "current_user": staff_user,
                    "grouped_categories": grouped_categories,
                    "selected_category_names": category_names,
                    "available_coaches": available_coaches,
                    "selected_coach_ids": coach_ids,
                    "error_message": "Seleziona fino a tre allenatori validi.",
                },
                status_code=400,
            )

    if is_recurring == "true":
        if not giorni or (not recurrence_count and not recurrence_end_date):
            grouped_categories = _group_categories(db)
            available_coaches = (
                db.query(models.User)
                .join(models.User.roles)
                .filter(models.Role.name == "allenatore")
                .order_by(models.User.first_name, models.User.last_name)
                .all()
            )
            return templates.TemplateResponse(
                "allenamenti/crea_allenamento.html",
                {
                    "request": request,
                    "current_user": staff_user,
                    "grouped_categories": grouped_categories,
                    "selected_category_names": category_names,
                    "available_coaches": available_coaches,
                    "selected_coach_ids": coach_ids,
                    "error_message": "Per la ricorrenza, selezionare i giorni e un numero di occorrenze o una data di fine.",
                },
                status_code=400,
            )
        byweekday = [DAY_MAP_DATETIL[d] for d in giorni if d in DAY_MAP_DATETIL]
        start_dt, end_dt = parse_orario(data, final_orario)
        duration = end_dt - start_dt
        rec_id = str(uuid.uuid4())
        rule_kwargs = {
            "dtstart": start_dt,
            "byweekday": byweekday,
        }
        if recurrence_end_date:
            rule_kwargs["until"] = datetime.combine(recurrence_end_date, start_dt.time())
        else:
            rule_kwargs["count"] = recurrence_count
        rule = rrule(WEEKLY, **rule_kwargs)
        for occ_dt in rule:
            new_a = models.Allenamento(
                tipo=tipo,
                descrizione=descrizione,
                data=occ_dt.date(),
                orario=f"{occ_dt.strftime('%H:%M')}-{(occ_dt + duration).strftime('%H:%M')}",
                recurrence_id=rec_id,
            )
            new_a.categories.extend(categories)
            new_a.coaches.extend(coaches)
            db.add(new_a)
    else:
        new_a = models.Allenamento(
            tipo=tipo,
            descrizione=descrizione,
            data=data,
            orario=final_orario,
        )
        new_a.categories.extend(categories)
        new_a.coaches.extend(coaches)
        db.add(new_a)
    db.commit()
    return RedirectResponse(url="/calendario", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/allenamenti/{id}/modifica", response_class=HTMLResponse)
async def modifica_allenamento_form(
    id: int,
    request: Request,
    db: Session = Depends(get_db),
    staff_user: models.User = Depends(get_current_admin_or_coach_user),
):
    allenamento = db.query(models.Allenamento).options(
        joinedload(models.Allenamento.categories),
        joinedload(models.Allenamento.coaches),
    ).get(id)
    if not allenamento:
        raise HTTPException(status_code=404, detail="Allenamento non trovato")
    grouped_categories = _group_categories(db)
    available_coaches = (
        db.query(models.User)
        .join(models.User.roles)
        .filter(models.Role.name == "allenatore")
        .order_by(models.User.first_name, models.User.last_name)
        .all()
    )
    selected_category_names = [c.nome for c in allenamento.categories]
    selected_coach_ids = [c.id for c in allenamento.coaches]
    return templates.TemplateResponse(
        "allenamenti/modifica_allenamento.html",
        {
            "request": request,
            "current_user": staff_user,
            "allenamento": allenamento,
            "grouped_categories": grouped_categories,
            "selected_category_names": selected_category_names,
            "available_coaches": available_coaches,
            "selected_coach_ids": selected_coach_ids,
        },
    )

@router.post("/allenamenti/{id}/modifica", response_class=RedirectResponse)
async def aggiorna_allenamento(
    id: int,
    request: Request,
    db: Session = Depends(get_db),
    staff_user: models.User = Depends(get_current_admin_or_coach_user),
    tipo: str = Form(...),
    descrizione: Optional[str] = Form(None),
    data: date = Form(...),
    orario: str = Form(...),
    orario_start: Optional[str] = Form(None),
    orario_end: Optional[str] = Form(None),
    category_names: List[str] = Form([]),
    coach_ids: List[int] = Form([]),
):
    allenamento = db.query(models.Allenamento).get(id)
    if not allenamento:
        raise HTTPException(status_code=404, detail="Allenamento non trovato")
    categories = (
        db.query(models.Categoria).filter(models.Categoria.nome.in_(category_names)).all()
        if category_names
        else []
    )
    if not categories or len(categories) != len(category_names):
        grouped_categories = _group_categories(db)
        return templates.TemplateResponse(
            "allenamenti/modifica_allenamento.html",
            {
                "request": request,
                "current_user": staff_user,
                "allenamento": allenamento,
                "grouped_categories": grouped_categories,
                "selected_category_names": category_names,
                "error_message": "Seleziona almeno una categoria valida.",
            },
            status_code=400,
        )
    if orario == "personalizzato":
        if not orario_start or not orario_end:
            grouped_categories = _group_categories(db)
            available_coaches = (
                db.query(models.User)
                .join(models.User.roles)
                .filter(models.Role.name == "allenatore")
                .order_by(models.User.first_name, models.User.last_name)
                .all()
            )
            return templates.TemplateResponse(
                "allenamenti/modifica_allenamento.html",
                {
                    "request": request,
                    "current_user": staff_user,
                    "allenamento": allenamento,
                    "grouped_categories": grouped_categories,
                    "selected_category_names": category_names,
                    "available_coaches": available_coaches,
                    "selected_coach_ids": coach_ids,
                    "error_message": "Specifica un orario di inizio e fine valido.",
                },
                status_code=400,
            )
        final_orario = f"{orario_start}-{orario_end}"
    else:
        final_orario = orario

    coaches = []
    if coach_ids:
        coaches = (
            db.query(models.User)
            .join(models.User.roles)
            .filter(models.Role.name == "allenatore", models.User.id.in_(coach_ids))
            .all()
        )
        if len(coaches) != len(coach_ids) or len(coach_ids) > 3:
            grouped_categories = _group_categories(db)
            available_coaches = (
                db.query(models.User)
                .join(models.User.roles)
                .filter(models.Role.name == "allenatore")
                .order_by(models.User.first_name, models.User.last_name)
                .all()
            )
            return templates.TemplateResponse(
                "allenamenti/modifica_allenamento.html",
                {
                    "request": request,
                    "current_user": staff_user,
                    "allenamento": allenamento,
                    "grouped_categories": grouped_categories,
                    "selected_category_names": category_names,
                    "available_coaches": available_coaches,
                    "selected_coach_ids": coach_ids,
                    "error_message": "Seleziona fino a tre allenatori validi.",
                },
                status_code=400,
            )

    allenamento.tipo = tipo
    allenamento.descrizione = descrizione
    allenamento.data = data
    allenamento.orario = final_orario
    allenamento.categories = categories
    allenamento.coaches = coaches
    db.commit()
    return RedirectResponse(url="/calendario", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/allenamenti/delete", response_class=RedirectResponse)
async def delete_allenamento_events(
    db: Session = Depends(get_db),
    staff_user: models.User = Depends(get_current_admin_or_coach_user),
    allenamento_id: int = Form(...),
    deletion_type: str = Form(...),
):
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
    type_filter: List[str] = Query([]),
    category_filter: List[str] = Query([]),
    user_category: Optional[str] = None,
    coach_filter: List[int] = Query([]),
    unassigned: bool = Query(False),
):
    query = db.query(models.Allenamento).options(
        joinedload(models.Allenamento.categories),
        joinedload(models.Allenamento.coaches),
    )

    if user_category or category_filter:
        query = query.join(models.Allenamento.categories)
    if category_filter:
        query = query.filter(models.Categoria.nome.in_(category_filter))
    if user_category:
        query = query.filter(models.Categoria.nome == user_category)
    if type_filter:
        query = query.filter(models.Allenamento.tipo.in_(type_filter))
    if coach_filter:
        query = query.join(models.Allenamento.coaches).filter(models.User.id.in_(coach_filter))
    elif unassigned:
        query = query.outerjoin(models.Allenamento.coaches).filter(models.User.id == None)

    events = []
    for a in query.distinct().all():
        start_dt, end_dt = parse_orario(a.data, a.orario)
        categories = ", ".join([c.nome for c in a.categories]) or "Nessuno"
        coaches = ", ".join([f"{c.first_name} {c.last_name}" for c in a.coaches]) or "Nessuno"
        events.append(
            {
                "id": a.id,
                "title": f"{a.tipo} - {a.descrizione}" if a.descrizione else a.tipo,
                "start": start_dt.isoformat(),
                "end": end_dt.isoformat(),
                "allDay": False,
                "backgroundColor": get_color_for_type(a.tipo),
                "borderColor": get_color_for_type(a.tipo),
                "extendedProps": {
                    "descrizione": a.descrizione,
                    "orario": a.orario,
                    "recurrence_id": a.recurrence_id,
                    "categories": categories,
                    "is_recurrent": "Sì" if a.recurrence_id else "No",
                    "coaches": coaches,
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
