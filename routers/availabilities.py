from collections import defaultdict
from datetime import date, timedelta
from typing import Dict, List

from fastapi import APIRouter, Depends, Request, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload

import models
from database import get_db
from dependencies import get_current_admin_or_coach_user, get_current_admin_user

router = APIRouter(tags=["Disponibilità Turni"])
templates = Jinja2Templates(directory="templates")


def _next_month_range() -> tuple[date, date]:
    today = date.today().replace(day=1)
    if today.month == 12:
        month_start = date(today.year + 1, 1, 1)
    else:
        month_start = date(today.year, today.month + 1, 1)
    if month_start.month == 12:
        next_month_start = date(month_start.year + 1, 1, 1)
    else:
        next_month_start = date(month_start.year, month_start.month + 1, 1)
    month_end = next_month_start - timedelta(days=1)
    return month_start, month_end


@router.get("/turni/disponibilita", response_class=HTMLResponse)
async def view_availabilities(
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_or_coach_user),
    user_id: int | None = None,
):
    month_start, month_end = _next_month_range()
    turni = (
        db.query(models.Turno)
        .filter(models.Turno.data.between(month_start, month_end))
        .order_by(models.Turno.data, models.Turno.fascia_oraria)
        .all()
    )
    grouped: Dict[date, Dict[str, models.Turno]] = defaultdict(dict)
    for t in turni:
        grouped[t.data][t.fascia_oraria] = t

    if current_user.is_admin and not user_id:
        availabilities = (
            db.query(models.TrainerAvailability)
            .join(models.Turno)
            .filter(models.Turno.data.between(month_start, month_end))
            .options(joinedload(models.TrainerAvailability.user), joinedload(models.TrainerAvailability.turno))
            .all()
        )
        coach_map: Dict[models.User, List[models.Turno]] = defaultdict(list)
        for av in availabilities:
            coach_map[av.user].append(av.turno)
        coaches = (
            db.query(models.User)
            .join(models.User.roles)
            .filter(models.Role.name == "allenatore")
            .order_by(models.User.first_name, models.User.last_name)
            .all()
        )
        return templates.TemplateResponse(
            request,
            "turni_disponibilita.html",
            {
                "current_user": current_user,
                "edit_user": None,
                "coach_map": coach_map,
                "coaches": coaches,
            },
        )
    else:
        edit_user = (
            db.get(models.User, user_id)
            if current_user.is_admin and user_id
            else current_user
        )
        if not edit_user or not edit_user.is_allenatore:
            raise HTTPException(status_code=404, detail="Allenatore non trovato")
        existing = (
            db.query(models.TrainerAvailability.turno_id)
            .filter(models.TrainerAvailability.user_id == edit_user.id)
            .join(models.Turno)
            .filter(models.Turno.data.between(month_start, month_end))
            .all()
        )
        selected_ids = {tid for (tid,) in existing}
        return templates.TemplateResponse(
            request,
            "turni_disponibilita.html",
            {
                "current_user": current_user,
                "edit_user": edit_user,
                "turni": grouped,
                "selected_ids": selected_ids,
            },
        )


@router.post("/turni/disponibilita", response_class=RedirectResponse)
async def save_availability(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_or_coach_user),
    turno_ids: List[int] = Form([]),
    user_id: int | None = Form(None),
):
    target_user_id = user_id if current_user.is_admin and user_id else current_user.id
    month_start, month_end = _next_month_range()
    turni_ids = [
        tid
        for (tid,) in db.query(models.Turno.id).filter(
            models.Turno.data.between(month_start, month_end)
        )
    ]
    db.query(models.TrainerAvailability).filter(
        models.TrainerAvailability.user_id == target_user_id,
        models.TrainerAvailability.turno_id.in_(turni_ids),
    ).delete(synchronize_session=False)
    for tid in turno_ids:
        db.add(models.TrainerAvailability(user_id=target_user_id, turno_id=tid, available=True))
    db.commit()
    redirect_url = "/turni/disponibilita"
    if current_user.is_admin:
        redirect_url += f"?user_id={target_user_id}"
    return RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER)


@router.post("/turni/disponibilita/proponi", response_class=RedirectResponse)
async def proponi_turni(
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(get_current_admin_user),
):
    turni = db.query(models.Turno).filter(models.Turno.user_id.is_(None)).all()
    for turno in turni:
        av = (
            db.query(models.TrainerAvailability)
            .filter(
                models.TrainerAvailability.turno_id == turno.id,
                models.TrainerAvailability.available.is_(True),
            )
            .first()
        )
        if av:
            turno.user_id = av.user_id
    db.commit()
    return RedirectResponse("/turni", status_code=status.HTTP_303_SEE_OTHER)
