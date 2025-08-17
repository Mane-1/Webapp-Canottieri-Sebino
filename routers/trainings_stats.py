from __future__ import annotations
from datetime import date
from io import StringIO
from typing import List, Optional
import csv

from fastapi import APIRouter, Depends, Query, Request, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import extract

import models
from database import get_db
from dependencies import get_current_admin_or_coach_user
from services.attendance_service import get_roster_for_training
from utils import parse_orario

router = APIRouter(tags=["Trainings Stats"])
templates = Jinja2Templates(directory="templates")


def _collect_stats(db: Session, year: int, month: int | None, categorie: List[str] | None, tipi: List[str] | None):
    query = db.query(models.Allenamento).filter(extract("year", models.Allenamento.data) == year)
    if month:
        query = query.filter(extract("month", models.Allenamento.data) == month)
    if tipi:
        query = query.filter(models.Allenamento.tipo.in_(tipi))
    trainings = query.options(joinedload(models.Allenamento.categories)).all()
    data = {
        "kpi": {"trainings": 0, "total_hours": 0.0, "present": 0, "absent": 0},
        "monthly": {},
        "by_type": {},
    }
    for t in trainings:
        if categorie and not any(c.nome in categorie for c in t.categories):
            continue
        roster = get_roster_for_training(db, t)
        roster_ids = {a.id for a in roster}
        absents = (
            db.query(models.Attendance)
            .filter(models.Attendance.training_id == t.id, models.Attendance.status == models.AttendanceStatus.absent, models.Attendance.athlete_id.in_(roster_ids))
            .count()
        )
        presents = len(roster_ids) - absents
        start, end = parse_orario(t.data, t.orario)
        hours = (end - start).total_seconds() / 3600
        data["kpi"]["trainings"] += 1
        data["kpi"]["total_hours"] += hours
        data["kpi"]["present"] += presents
        data["kpi"]["absent"] += absents
        m = t.data.month
        monthly = data["monthly"].setdefault(m, {"trainings": 0, "hours": 0.0, "present": 0, "absent": 0})
        monthly["trainings"] += 1
        monthly["hours"] += hours
        monthly["present"] += presents
        monthly["absent"] += absents
        bt = data["by_type"].setdefault(t.tipo, {"trainings": 0, "hours": 0.0, "present": 0, "absent": 0})
        bt["trainings"] += 1
        bt["hours"] += hours
        bt["present"] += presents
        bt["absent"] += absents
    monthly_list = [
        {
            "month": m,
            "trainings": d["trainings"],
            "hours": d["hours"],
            "present": d["present"],
            "absent": d["absent"],
        }
        for m, d in sorted(data["monthly"].items())
    ]
    by_type_list = [
        {
            "type": t,
            "trainings": d["trainings"],
            "hours": d["hours"],
            "present": d["present"],
            "absent": d["absent"],
        }
        for t, d in sorted(data["by_type"].items())
    ]
    return {
        "kpi": data["kpi"],
        "monthly": monthly_list,
        "by_type": by_type_list,
    }


@router.get("/trainings/stats", name="trainings_stats")
def trainings_stats_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_or_coach_user),
):
    current_year = date.today().year
    years = list(range(current_year, current_year - 5, -1))
    categories = db.query(models.Categoria).order_by(models.Categoria.nome).all()
    types = [
        t[0]
        for t in db.query(models.Allenamento.tipo)
        .distinct()
        .order_by(models.Allenamento.tipo)
    ]
    return templates.TemplateResponse(
        "trainings/stats.html",
        {
            "request": request,
            "current_user": current_user,
            "years": years,
            "current_year": current_year,
            "categories": categories,
            "types": types,
        },
    )


@router.get("/api/trainings/stats")
def trainings_stats_api(
    year: int = Query(...),
    month: Optional[int] = Query(None),
    categoria: Optional[List[str]] = Query(None),
    tipo: Optional[List[str]] = Query(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_or_coach_user),
):
    return _collect_stats(db, year, month, categoria, tipo)


@router.get("/api/trainings/stats.csv")
def trainings_stats_csv(
    year: int = Query(...),
    month: Optional[int] = Query(None),
    categoria: Optional[List[str]] = Query(None),
    tipo: Optional[List[str]] = Query(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_or_coach_user),
):
    stats = _collect_stats(db, year, month, categoria, tipo)
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["month", "trainings", "hours", "present", "absent"])
    for row in stats["monthly"]:
        writer.writerow([row["month"], row["trainings"], row["hours"], row["present"], row["absent"]])
    response = Response(content=output.getvalue(), media_type="text/csv; charset=utf-8")
    response.headers["Content-Disposition"] = "attachment; filename=trainings_stats.csv"
    return response
