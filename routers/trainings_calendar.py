from __future__ import annotations
from datetime import date, time, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import and_
from sqlalchemy.orm import Session, selectinload

import models
from database import get_db
from utils.dates import week_bounds, expand_occurrences

router = APIRouter(prefix="/trainings", tags=["trainings"])
templates = Jinja2Templates(directory="templates")

def _parse_week(week: Optional[str]) -> tuple[int, int]:
    if not week:
        today = date.today()
        y, w, _ = today.isocalendar()
        return y, w
    y, w = week.split("-W")
    return int(y), int(w)

@router.get("/calendar", response_class=HTMLResponse, name="calendar_view")
def calendar_view(request: Request, week: Optional[str] = None, coach_id: Optional[int] = None, db: Session = Depends(get_db)):
    year, isoweek = _parse_week(week)
    start, end = week_bounds(year, isoweek)
    query = (
        db.query(models.Allenamento)
        .options(selectinload(models.Allenamento.barca), selectinload(models.Allenamento.coach))
        .filter(models.Allenamento.data.between(start, end))
    )
    if coach_id:
        query = query.filter(models.Allenamento.coach_id == coach_id)
    trainings = query.all()
    occurrences = []
    for t in trainings:
        occs = expand_occurrences(t, (start, end))
        for occ in occs:
            occ["coach_id"] = t.coach_id
            occ["coach_name"] = f"{t.coach.first_name} {t.coach.last_name}" if t.coach else None
        occurrences.extend(occs)
    coaches = (
        db.query(models.User)
        .join(models.User.roles)
        .filter(models.Role.name == "allenatore")
        .all()
    )
    return templates.TemplateResponse(
        request,
        "calendar.html",
        {
            "week_start": start,
            "week_end": end,
            "year": year,
            "isoweek": isoweek,
            "occurrences": occurrences,
            "timedelta": timedelta,
            "coaches": coaches,
            "selected_coach": coach_id,
        },
    )

@router.post("", status_code=303)
def create_training(
    tipo: str = Form(...),
    descrizione: Optional[str] = Form(None),
    date_: date = Form(..., alias="date"),
    time_start: str = Form(...),
    time_end: str = Form(...),
    recurrence: Optional[str] = Form(None),
    repeat_until: Optional[date] = Form(None),
    barca_id: Optional[int] = Form(None),
    coach_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
):
    ts = time.fromisoformat(time_start)
    te = time.fromisoformat(time_end)
    if te <= ts:
        raise HTTPException(status_code=400, detail="Ora fine deve essere > ora inizio")
    conflict_filters = [models.Allenamento.data == date_]
    if barca_id:
        conflict_filters.append(models.Allenamento.barca_id == barca_id)
    if coach_id:
        conflict_filters.append(models.Allenamento.coach_id == coach_id)
    if len(conflict_filters) > 1:
        existing = db.query(models.Allenamento).filter(and_(*conflict_filters)).all()
        for e in existing:
            if e.time_start and e.time_end:
                if not (te <= e.time_start or ts >= e.time_end):
                    raise HTTPException(status_code=409, detail="Conflitto di orario con barca/coach")
    t = models.Allenamento(
        tipo=tipo,
        descrizione=descrizione,
        data=date_,
        time_start=ts,
        time_end=te,
        recurrence=recurrence,
        repeat_until=repeat_until,
        barca_id=barca_id,
        coach_id=coach_id,
    )
    db.add(t)
    db.commit()
    return RedirectResponse(url="/trainings/calendar", status_code=303)
