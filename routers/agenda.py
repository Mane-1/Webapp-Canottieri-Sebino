# File: routers/agenda.py
from datetime import date, timedelta
from typing import Dict, List

from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

import models
from database import get_db
from utils.dates import human_day_label
from utils import get_color_for_type

router = APIRouter(tags=["Agenda"])
templates = Jinja2Templates(directory="templates")


def normalize_event(e) -> Dict:
    if hasattr(e, "data"):
        d = e.data
    else:
        d = getattr(e, "data", None)
    time_str = getattr(e, "orario", None) or getattr(e, "fascia_oraria", "")
    etype = "allenamento" if isinstance(e, models.Allenamento) else "turno"
    title = getattr(e, "tipo", None) or (f"Turno {time_str}" if etype == "turno" else "Allenamento")
    cats = [c.nome for c in getattr(e, "categories", [])]
    color = get_color_for_type(getattr(e, "tipo", None))
    return {
        "id": e.id,
        "date": d,
        "time_str": time_str,
        "title": title,
        "type": etype,
        "categories": cats,
        "color": color,
        "duration_minutes": None,
    }


def daterange(base: date, days: int = 7):
    return base, base + timedelta(days=days - 1)


@router.get("/agenda", response_class=HTMLResponse)
def agenda_page(
    request: Request,
    date_str: str | None = Query(None, description="YYYY-MM-DD; default=today"),
    type: str = Query("all", pattern="^(all|allenamenti|turni)$"),
    db: Session = Depends(get_db),
):
    base = date.fromisoformat(date_str) if date_str else date.today()
    start, end = daterange(base, days=7)

    items: List = []
    if type in ("all", "allenamenti"):
        als = (
            db.query(models.Allenamento)
            .filter(models.Allenamento.data.between(start, end))
            .order_by(models.Allenamento.data.asc())
            .all()
        )
        items.extend(als)
    if type in ("all", "turni"):
        trs = (
            db.query(models.Turno)
            .filter(models.Turno.data.between(start, end))
            .order_by(models.Turno.data.asc())
            .all()
        )
        items.extend(trs)

    normalized = [normalize_event(e) for e in items]
    grouped: Dict[date, List[Dict]] = {}
    for ev in normalized:
        grouped.setdefault(ev["date"], []).append(ev)

    days = []
    for i in range(7):
        d = start + timedelta(days=i)
        days.append(
            {
                "date": d,
                "human": human_day_label(d),
                "events": sorted(grouped.get(d, []), key=lambda x: (x["time_str"], x["title"])),
            }
        )

    prev_date = (base - timedelta(days=7)).isoformat()
    next_date = (base + timedelta(days=7)).isoformat()
    load_more_date = (days[-1]["date"] + timedelta(days=1)).isoformat()

    return templates.TemplateResponse(
        "agenda.html",
        {
            "request": request,
            "days": days,
            "current_date": base,
            "current_date_str": human_day_label(base),
            "prev_date": prev_date,
            "next_date": next_date,
            "q_type": type,
            "load_more_date": load_more_date,
        },
    )


@router.get("/api/agenda")
def agenda_api(
    date_from: str,
    date_to: str,
    type: str = Query("all", pattern="^(all|allenamenti|turni)$"),
    db: Session = Depends(get_db),
):
    start = date.fromisoformat(date_from)
    end = date.fromisoformat(date_to)

    items: List = []
    if type in ("all", "allenamenti"):
        items += db.query(models.Allenamento).filter(models.Allenamento.data.between(start, end)).all()
    if type in ("all", "turni"):
        items += db.query(models.Turno).filter(models.Turno.data.between(start, end)).all()

    data = [normalize_event(e) for e in items]
    return {"from": start.isoformat(), "to": end.isoformat(), "type": type, "items": data}
