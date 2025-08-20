"""Calendar and agenda related routes."""
from datetime import date, datetime, timedelta, time, timezone
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends, HTTPException, Response, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

import models
from database import get_db
from dependencies import get_current_user
from utils import parse_orario, get_color_for_type
from services.calendar_service import (
    get_or_create_calendar_token,
    rotate_calendar_token,
)
from services.attendance_service import get_roster_for_training

router = APIRouter(tags=["Calendario"])
templates = Jinja2Templates(directory="templates")
TZ = ZoneInfo("Europe/Rome")


def _fmt_dt(dt: datetime) -> str:
    return dt.strftime("%Y%m%dT%H%M%S")


def _escape(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
        .replace(",", "\\,")
        .replace(";", "\\;")
        .replace("\n", "\\n")
    )


def _event(uid: str, start: datetime, end: datetime, summary: str, description: str) -> str:
    lines = [
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}",
        f"DTSTART;TZID=Europe/Rome:{_fmt_dt(start)}",
        f"DTEND;TZID=Europe/Rome:{_fmt_dt(end)}",
        "STATUS:CONFIRMED",
        "TRANSP:OPAQUE",
        f"SUMMARY:{_escape(summary)}",
        f"DESCRIPTION:{_escape(description)}" if description else "DESCRIPTION:",
        "LOCATION:Canottieri Sebino",
        "END:VEVENT",
    ]
    return "\r\n".join(lines)


@router.get("/calendar/{token}.ics", include_in_schema=False)
def calendar_ics(token: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter_by(calendar_token=token).first()
    if not user:
        raise HTTPException(status_code=404, detail="Token non valido")
    today = date.today()
    start_date = today - timedelta(days=60)
    end_date = today + timedelta(days=270)
    events: list[str] = []

    if user.is_allenatore:
        turni = (
            db.query(models.Turno)
            .filter(
                models.Turno.user_id == user.id,
                models.Turno.data >= start_date,
                models.Turno.data <= end_date,
            )
            .order_by(models.Turno.data)
            .all()
        )
        for t in turni:
            start_hour, end_hour = (8, 12) if t.fascia_oraria == "Mattina" else (17, 21)
            start_dt = datetime.combine(t.data, time(start_hour), tzinfo=TZ)
            end_dt = datetime.combine(t.data, time(end_hour), tzinfo=TZ)
            summary = "APERTURA CANOTTIERI"
            events.append(
                _event(
                    f"turno-{t.id}@sebino",
                    start_dt,
                    end_dt,
                    summary,
                    "",
                )
            )

    trainings_added: set[int] = set()
    trainings = (
        db.query(models.Allenamento)
        .filter(
            models.Allenamento.data >= start_date,
            models.Allenamento.data <= end_date,
        )
        .all()
    )
    for a in trainings:
        include = False
        if user.is_allenatore and any(c.id == user.id for c in a.coaches):
            include = True
        if not include and user.is_atleta:
            roster = get_roster_for_training(db, a)
            if any(u.id == user.id for u in roster):
                include = True
        if not include or a.id in trainings_added:
            continue
        trainings_added.add(a.id)
        start_dt, end_dt = parse_orario(a.data, a.orario)
        start_dt = start_dt.replace(tzinfo=TZ)
        end_dt = end_dt.replace(tzinfo=TZ)
        summary = a.tipo
        if a.descrizione:
            summary = f"{a.tipo} - {a.descrizione}"
        cat_parts = [c.nome for c in a.categories]
        if a.barca:
            cat_parts.extend(
                f"{u.first_name} {u.last_name}" for u in a.barca.atleti_assegnati
            )
        desc_lines = []
        desc_lines.append(
            "Categorie assegnate: " + ", ".join(cat_parts)
            if cat_parts
            else "Categorie assegnate:"
        )
        coach_names = ", ".join(f"{c.first_name} {c.last_name}" for c in a.coaches)
        desc_lines.append(
            "Allenatori: " + coach_names if coach_names else "Allenatori:"
        )
        description = "\n".join(desc_lines)
        events.append(
            _event(
                f"training-{a.id}@sebino",
                start_dt,
                end_dt,
                summary,
                description,
            )
        )

    ics_lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Canottieri Sebino//Agenda//IT",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:Agenda Canottieri",
        "X-WR-TIMEZONE:Europe/Rome",
    ] + events + ["END:VCALENDAR"]
    content = "\r\n".join(ics_lines) + "\r\n"
    headers = {"Cache-Control": "private, max-age=300"}
    return Response(content=content, media_type="text/calendar; charset=utf-8", headers=headers)


@router.get("/api/calendar/link")
def api_calendar_link(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    token = get_or_create_calendar_token(db, current_user)
    return {"ics_url": f"/calendar/{token}.ics"}


@router.post("/api/calendar/regenerate")
def api_calendar_regenerate(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    token = rotate_calendar_token(db, current_user)
    return {"ics_url": f"/calendar/{token}.ics"}


@router.get("/agenda", response_class=HTMLResponse)
def agenda_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    coaches = []
    if current_user.is_admin:
        coaches = (
            db.query(models.User)
            .join(models.User.roles)
            .filter(models.Role.name == "allenatore")
            .all()
        )
    return templates.TemplateResponse(
        request,
        "agenda.html",
        {"current_user": current_user, "allenatori": coaches},
    )


@router.get("/api/agenda")
def agenda_events(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    today = date.today()
    start_date = today - timedelta(days=60)
    end_date = today + timedelta(days=270)
    events = []

    if current_user.is_allenatore:
        turni = (
            db.query(models.Turno)
            .filter(
                models.Turno.user_id == current_user.id,
                models.Turno.data >= start_date,
                models.Turno.data <= end_date,
            )
            .all()
        )
        availabilities = (
            db.query(models.TrainerAvailability)
            .filter(
                models.TrainerAvailability.turno_id.in_([t.id for t in turni]),
                models.TrainerAvailability.available.is_(True),
            )
            .all()
        )
        avail_map: dict[int, list[int]] = {}
        for av in availabilities:
            avail_map.setdefault(av.turno_id, []).append(av.user_id)
        for t in turni:
            start_hour, end_hour = (8, 12) if t.fascia_oraria == "Mattina" else (17, 21)
            start_dt = datetime.combine(t.data, time(start_hour), tzinfo=TZ)
            end_dt = datetime.combine(t.data, time(end_hour), tzinfo=TZ)
            events.append(
                {
                    "id": f"turno-{t.id}",
                    "title": "APERTURA CANOTTIERI",
                    "start": start_dt.isoformat(),
                    "end": end_dt.isoformat(),
                    "backgroundColor": "#0d6efd",
                    "extendedProps": {
                        "user_id": t.user_id,
                        "fascia_oraria": t.fascia_oraria,
                        "available_ids": avail_map.get(t.id, []),
                    },
                }
            )

    trainings_added: set[int] = set()
    trainings = (
        db.query(models.Allenamento)
        .filter(
            models.Allenamento.data >= start_date,
            models.Allenamento.data <= end_date,
        )
        .all()
    )
    for a in trainings:
        include = False
        if current_user.is_allenatore and any(c.id == current_user.id for c in a.coaches):
            include = True
        if not include and current_user.is_atleta:
            roster = get_roster_for_training(db, a)
            if any(u.id == current_user.id for u in roster):
                include = True
        if not include or a.id in trainings_added:
            continue
        trainings_added.add(a.id)
        start_dt, end_dt = parse_orario(a.data, a.orario)
        start_dt = start_dt.replace(tzinfo=TZ)
        end_dt = end_dt.replace(tzinfo=TZ)
        title = a.tipo if not a.descrizione else f"{a.tipo} - {a.descrizione}"
        categories = ", ".join([c.nome for c in a.categories]) or "Nessuno"
        coaches = ", ".join(
            [f"{c.first_name} {c.last_name}" for c in a.coaches]
        ) or "Nessuno"
        events.append(
            {
                "id": f"training-{a.id}",
                "title": title,
                "start": start_dt.isoformat(),
                "end": end_dt.isoformat(),
                "backgroundColor": get_color_for_type(a.tipo),
                "extendedProps": {
                    "descrizione": a.descrizione,
                    "orario": a.orario,
                    "recurrence_id": a.recurrence_id,
                    "categories": categories,
                    "coaches": coaches,
                },
            }
        )
    return events
