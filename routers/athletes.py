"""Routes related to athletes management."""
from datetime import date
from io import StringIO
from typing import List, Optional
import csv

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import extract, or_

import models
from schemas.athletes import MeasurementIn
from database import get_db
from dependencies import get_current_admin_or_coach_user
from services.athletes_service import (
    current_category_for_user,
    get_athlete_attendance_stats,
)
from services.attendance_service import (
    get_roster_for_training,
    compute_status_for_athlete,
)

router = APIRouter(tags=["Atleti"])
templates = Jinja2Templates(directory="templates")


@router.get("/risorse/athletes", name="athletes_list")
def athletes_list(
    request: Request,
    q: Optional[str] = Query(None),
    categoria: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_or_coach_user),
):
    categories = db.query(models.Categoria).order_by(models.Categoria.nome).all()
    query = (
        db.query(models.User)
        .join(models.User.roles)
        .filter(models.Role.name == "atleta")
    )
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                models.User.first_name.ilike(like),
                models.User.last_name.ilike(like),
                models.User.email.ilike(like),
                models.User.tax_code.ilike(like),
            )
        )
    today = date.today()
    users = query.order_by(models.User.last_name, models.User.first_name).all()
    rows = []
    for u in users:
        cat = current_category_for_user(db, u, today)
        if categoria and (not cat or cat.nome != categoria):
            continue
        rows.append({"user": u, "category": cat.nome if cat else None})
    return templates.TemplateResponse(
        request,
        "athletes/index.html",
        {
            "current_user": current_user,
            "rows": rows,
            "q": q,
            "categoria": categoria,
            "categories": categories,
            "today": today,
        },
    )


@router.get("/api/athletes")
def api_all_athletes(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_or_coach_user),
):
    athletes = (
        db.query(models.User)
        .join(models.User.roles)
        .filter(models.Role.name == "atleta")
        .order_by(models.User.last_name, models.User.first_name)
        .all()
    )
    return [{"id": a.id, "name": f"{a.first_name} {a.last_name}"} for a in athletes]


@router.get("/api/athletes")
def api_all_athletes(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_or_coach_user),
):
    athletes = (
        db.query(models.User)
        .join(models.User.roles)
        .filter(models.Role.name == "atleta")
        .order_by(models.User.last_name, models.User.first_name)
        .all()
    )
    return [{"id": a.id, "name": f"{a.first_name} {a.last_name}"} for a in athletes]


@router.get("/api/categories")
def api_all_categories(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_or_coach_user),
):
    categories = (
        db.query(models.Categoria)
        .order_by(models.Categoria.ordine)
        .all()
    )
    return [
        {"id": c.id, "name": c.nome, "group": c.macro_group or ""}
        for c in categories
    ]


@router.get("/api/athletes")
def api_all_athletes(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_or_coach_user),
):
    athletes = (
        db.query(models.User)
        .join(models.User.roles)
        .filter(models.Role.name == "atleta")
        .order_by(models.User.last_name, models.User.first_name)
        .all()
    )
    return [{"id": a.id, "name": f"{a.first_name} {a.last_name}"} for a in athletes]


@router.get("/api/categories")
def api_all_categories(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_or_coach_user),
):
    categories = (
        db.query(models.Categoria)
        .order_by(models.Categoria.ordine)
        .all()
    )
    return [
        {"id": c.id, "name": c.nome, "group": c.macro_group or ""}
        for c in categories
    ]


@router.get("/api/athletes")
def api_all_athletes(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_or_coach_user),
):
    athletes = (
        db.query(models.User)
        .join(models.User.roles)
        .filter(models.Role.name == "atleta")
        .order_by(models.User.last_name, models.User.first_name)
        .all()
    )
    return [{"id": a.id, "name": f"{a.first_name} {a.last_name}"} for a in athletes]


@router.get("/api/categories")
def api_all_categories(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_or_coach_user),
):
    categories = (
        db.query(models.Categoria)
        .order_by(models.Categoria.ordine)
        .all()
    )
    return [
        {"id": c.id, "name": c.nome, "group": c.macro_group or ""}
        for c in categories
    ]


@router.get("/api/athletes")
def api_all_athletes(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_or_coach_user),
):
    athletes = (
        db.query(models.User)
        .join(models.User.roles)
        .filter(models.Role.name == "atleta")
        .order_by(models.User.last_name, models.User.first_name)
        .all()
    )
    return [{"id": a.id, "name": f"{a.first_name} {a.last_name}"} for a in athletes]


@router.get("/api/categories")
def api_all_categories(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_or_coach_user),
):
    categories = (
        db.query(models.Categoria)
        .order_by(models.Categoria.ordine)
        .all()
    )
    return [
        {"id": c.id, "name": c.nome, "group": c.macro_group or ""}
        for c in categories
    ]


@router.get("/api/athletes")
def api_all_athletes(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_or_coach_user),
):
    athletes = (
        db.query(models.User)
        .join(models.User.roles)
        .filter(models.Role.name == "atleta")
        .order_by(models.User.last_name, models.User.first_name)
        .all()
    )
    return [{"id": a.id, "name": f"{a.first_name} {a.last_name}"} for a in athletes]


@router.get("/api/categories")
def api_all_categories(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_or_coach_user),
):
    categories = (
        db.query(models.Categoria)
        .order_by(models.Categoria.ordine)
        .all()
    )
    return [
        {"id": c.id, "name": c.nome, "group": c.macro_group or ""}
        for c in categories
    ]


@router.get("/api/athletes")
def api_all_athletes(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_or_coach_user),
):
    athletes = (
        db.query(models.User)
        .join(models.User.roles)
        .filter(models.Role.name == "atleta")
        .order_by(models.User.last_name, models.User.first_name)
        .all()
    )
    return [{"id": a.id, "name": f"{a.first_name} {a.last_name}"} for a in athletes]


@router.get("/api/categories")
def api_all_categories(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_or_coach_user),
):
    categories = (
        db.query(models.Categoria)
        .order_by(models.Categoria.ordine)
        .all()
    )
    return [
        {"id": c.id, "name": c.nome, "group": c.macro_group or ""}
        for c in categories
    ]


@router.get("/risorse/athletes/{athlete_id}", name="athlete_detail")
def athlete_detail(
    request: Request,
    athlete_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_or_coach_user),
):
    athlete = db.get(models.User, athlete_id)
    if not athlete:
        raise HTTPException(status_code=404, detail="Athlete not found")
    category = current_category_for_user(db, athlete, date.today())
    measurements = (
        db.query(models.AthleteMeasurement)
        .filter_by(athlete_id=athlete_id)
        .order_by(models.AthleteMeasurement.measured_at.desc())
        .limit(51)
        .all()
    )
    measurement_rows = []
    for idx, m in enumerate(measurements[:50]):
        prev = measurements[idx + 1] if idx + 1 < len(measurements) else None
        diff_w = (
            m.weight_kg - prev.weight_kg
            if prev and m.weight_kg is not None and prev.weight_kg is not None
            else None
        )
        diff_h = (
            m.height_cm - prev.height_cm
            if prev and m.height_cm is not None and prev.height_cm is not None
            else None
        )
        measurement_rows.append({"m": m, "diff_weight": diff_w, "diff_height": diff_h})

    trainings = (
        db.query(models.Allenamento)
        .order_by(models.Allenamento.data.desc(), models.Allenamento.id.desc())
        .limit(200)
        .all()
    )
    attendance_rows = []
    assigned = present = 0
    for t in trainings:
        roster = get_roster_for_training(db, t)
        if athlete not in roster:
            continue
        assigned += 1
        status = compute_status_for_athlete(db, t.id, athlete.id).value
        if status == 'present':
            present += 1
        attendance_rows.append(
            {
                "date": t.data,
                "orario": t.orario,
                "tipo": t.tipo,
                "descrizione": t.descrizione,
                "status": status,
            }
        )
        if len(attendance_rows) >= 50:
            break
    rate = present / assigned if assigned else 0

    return templates.TemplateResponse(
        request,
        "athletes/detail.html",
        {
            "current_user": current_user,
            "athlete": athlete,
            "category": category.nome if category else None,
            "measurement_rows": measurement_rows,
            "attendance_rows": attendance_rows,
            "att_stats": {"assigned": assigned, "present": present, "rate": rate},
            "today": date.today(),
        },
    )


@router.post("/risorse/athletes/{athlete_id}/measurements")
async def add_measurement(
    athlete_id: int,
    payload: MeasurementIn,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_or_coach_user),
):
    athlete = db.get(models.User, athlete_id)
    if not athlete:
        raise HTTPException(status_code=404, detail="Athlete not found")
    measured_at = payload.measured_at or date.today()
    measurement = models.AthleteMeasurement(
        athlete_id=athlete_id,
        measured_at=measured_at,
        height_cm=payload.height_cm,
        weight_kg=payload.weight_kg,
        torso_height_cm=payload.torso_height_cm,
        wingspan_cm=payload.wingspan_cm,
        leg_length_cm=payload.leg_length_cm,
        tibia_length_cm=payload.tibia_length_cm,
        arm_length_cm=payload.arm_length_cm,
        foot_length_cm=payload.foot_length_cm,
        flexibility_cm=payload.flexibility_cm,
        notes=payload.notes,
        recorded_by_user_id=current_user.id,
    )
    db.add(measurement)
    db.commit()
    db.refresh(measurement)
    return {
        "id": measurement.id,
        "measured_at": measurement.measured_at.isoformat(),
        "height_cm": measurement.height_cm,
        "weight_kg": measurement.weight_kg,
        "torso_height_cm": measurement.torso_height_cm,
        "wingspan_cm": measurement.wingspan_cm,
        "leg_length_cm": measurement.leg_length_cm,
        "tibia_length_cm": measurement.tibia_length_cm,
        "arm_length_cm": measurement.arm_length_cm,
        "foot_length_cm": measurement.foot_length_cm,
        "flexibility_cm": measurement.flexibility_cm,
        "notes": measurement.notes,
    }


@router.get("/api/athletes/{athlete_id}/measurements")
async def measurements_series(
    athlete_id: int,
    metric: str = Query(...),
    year: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_or_coach_user),
):
    q = db.query(models.AthleteMeasurement).filter_by(athlete_id=athlete_id)
    if year is not None:
        q = q.filter(extract('year', models.AthleteMeasurement.measured_at) == year)
    q = q.order_by(models.AthleteMeasurement.measured_at.asc())
    measurements = q.all()
    labels = [m.measured_at.isoformat() for m in measurements]
    
    metric_mapping = {
        "weight": "weight_kg",
        "height": "height_cm",
        "torso_height": "torso_height_cm",
        "wingspan": "wingspan_cm",
        "leg_length": "leg_length_cm",
        "tibia_length": "tibia_length_cm",
        "arm_length": "arm_length_cm",
        "foot_length": "foot_length_cm",
        "flexibility": "flexibility_cm"
    }
    
    field_name = metric_mapping.get(metric)
    if field_name:
        data = [getattr(m, field_name) for m in measurements]
    else:
        data = []
    
    return {"labels": labels, "data": data}


@router.put("/risorse/athletes/{athlete_id}/measurements/{measurement_id}")
async def update_measurement(
    athlete_id: int,
    measurement_id: int,
    payload: MeasurementIn,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_or_coach_user),
):
    measurement = db.query(models.AthleteMeasurement).filter_by(
        id=measurement_id, athlete_id=athlete_id
    ).first()
    if not measurement:
        raise HTTPException(status_code=404, detail="Measurement not found")
    
    # Update fields
    if payload.measured_at is not None:
        measurement.measured_at = payload.measured_at
    if payload.height_cm is not None:
        measurement.height_cm = payload.height_cm
    if payload.weight_kg is not None:
        measurement.weight_kg = payload.weight_kg
    if payload.torso_height_cm is not None:
        measurement.torso_height_cm = payload.torso_height_cm
    if payload.wingspan_cm is not None:
        measurement.wingspan_cm = payload.wingspan_cm
    if payload.leg_length_cm is not None:
        measurement.leg_length_cm = payload.leg_length_cm
    if payload.tibia_length_cm is not None:
        measurement.tibia_length_cm = payload.tibia_length_cm
    if payload.arm_length_cm is not None:
        measurement.arm_length_cm = payload.arm_length_cm
    if payload.foot_length_cm is not None:
        measurement.foot_length_cm = payload.foot_length_cm
    if payload.flexibility_cm is not None:
        measurement.flexibility_cm = payload.flexibility_cm
    if payload.notes is not None:
        measurement.notes = payload.notes
    
    db.commit()
    db.refresh(measurement)
    return {
        "id": measurement.id,
        "measured_at": measurement.measured_at.isoformat(),
        "height_cm": measurement.height_cm,
        "weight_kg": measurement.weight_kg,
        "torso_height_cm": measurement.torso_height_cm,
        "wingspan_cm": measurement.wingspan_cm,
        "leg_length_cm": measurement.leg_length_cm,
        "tibia_length_cm": measurement.tibia_length_cm,
        "arm_length_cm": measurement.arm_length_cm,
        "foot_length_cm": measurement.foot_length_cm,
        "flexibility_cm": measurement.flexibility_cm,
        "notes": measurement.notes,
    }


@router.delete("/risorse/athletes/{athlete_id}/measurements/{measurement_id}")
async def delete_measurement(
    athlete_id: int,
    measurement_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_or_coach_user),
):
    measurement = db.query(models.AthleteMeasurement).filter_by(
        id=measurement_id, athlete_id=athlete_id
    ).first()
    if not measurement:
        raise HTTPException(status_code=404, detail="Measurement not found")
    
    db.delete(measurement)
    db.commit()
    return {"message": "Measurement deleted successfully"}


@router.get("/risorse/athletes/{athlete_id}/measurements")
async def get_athlete_measurements(
    athlete_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_or_coach_user),
):
    measurements = db.query(models.AthleteMeasurement).filter_by(
        athlete_id=athlete_id
    ).order_by(models.AthleteMeasurement.measured_at.desc()).all()
    
    return [
        {
            "id": m.id,
            "measured_at": m.measured_at.isoformat(),
            "height_cm": m.height_cm,
            "weight_kg": m.weight_kg,
            "torso_height_cm": m.torso_height_cm,
            "wingspan_cm": m.wingspan_cm,
            "leg_length_cm": m.leg_length_cm,
            "tibia_length_cm": m.tibia_length_cm,
            "arm_length_cm": m.arm_length_cm,
            "foot_length_cm": m.foot_length_cm,
            "flexibility_cm": m.flexibility_cm,
            "notes": m.notes,
        }
        for m in measurements
    ]


@router.get("/api/athletes/{athlete_id}/attendance_stats")
def athlete_attendance_stats(
    athlete_id: int,
    year: int = Query(...),
    month: Optional[int] = Query(None),
    tipo: Optional[List[str]] = Query(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_or_coach_user),
):
    stats = get_athlete_attendance_stats(db, athlete_id, year, month, tipo)
    return stats


@router.get("/api/athletes/{athlete_id}/attendance.csv")
def athlete_attendance_csv(
    athlete_id: int,
    year: int = Query(...),
    month: Optional[int] = Query(None),
    tipo: Optional[List[str]] = Query(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_or_coach_user),
):
    stats = get_athlete_attendance_stats(db, athlete_id, year, month, tipo)
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["date", "tipo", "categories", "status", "source", "change_count", "time_range"])
    for s in stats["sessions"]:
        writer.writerow(
            [
                s["date"],
                s["tipo"],
                ",".join(s["categories"]),
                s["status"],
                s["source"],
                s["change_count"],
                s.get("time_range"),
            ]
        )
    response = Response(content=output.getvalue(), media_type="text/csv; charset=utf-8")
    response.headers["Content-Disposition"] = (
        f"attachment; filename=athlete_{athlete_id}_attendance.csv"
    )
    return response
