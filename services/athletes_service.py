from __future__ import annotations
from datetime import date
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import extract

import models
from services.attendance_service import get_roster_for_training, compute_status_for_athlete


def current_category_for_user(db: Session, user: models.User, ref: date) -> Optional[models.Categoria]:
    if not user.date_of_birth:
        return None
    age = ref.year - user.date_of_birth.year - (
        (ref.month, ref.day) < (user.date_of_birth.month, user.date_of_birth.day)
    )
    return (
        db.query(models.Categoria)
        .filter(models.Categoria.eta_min <= age, models.Categoria.eta_max >= age)
        .first()
    )


def get_athlete_attendance_stats(
    db: Session, athlete_id: int, year: int, month: int | None = None, tipi: List[str] | None = None
) -> dict:
    trainings_query = db.query(models.Allenamento).filter(
        extract("year", models.Allenamento.data) == year
    )
    if month:
        trainings_query = trainings_query.filter(extract("month", models.Allenamento.data) == month)
    if tipi:
        trainings_query = trainings_query.filter(models.Allenamento.tipo.in_(tipi))
    trainings = trainings_query.options(joinedload(models.Allenamento.categories)).all()

    athlete = db.get(models.User, athlete_id)
    if not athlete:
        raise ValueError("Athlete not found")

    kpi = {"sessions": 0, "present": 0, "absent": 0}
    monthly: dict[int, dict[str, int]] = {}
    by_type: dict[str, dict[str, int]] = {}
    sessions_list: list[dict] = []

    for training in trainings:
        roster = get_roster_for_training(db, training)
        if athlete not in roster:
            continue
        status = compute_status_for_athlete(db, training.id, athlete_id)
        attendance = (
            db.query(models.Attendance)
            .filter_by(training_id=training.id, athlete_id=athlete_id)
            .first()
        )
        if attendance:
            source = attendance.source
            change_count = attendance.change_count
        else:
            source = models.AttendanceSource.system
            change_count = 0
        kpi["sessions"] += 1
        if status == models.AttendanceStatus.present:
            kpi["present"] += 1
        else:
            kpi["absent"] += 1
        month_idx = training.data.month
        monthly.setdefault(month_idx, {"present": 0, "absent": 0})
        if status == models.AttendanceStatus.present:
            monthly[month_idx]["present"] += 1
        else:
            monthly[month_idx]["absent"] += 1
        by_type.setdefault(training.tipo, {"present": 0, "absent": 0})
        if status == models.AttendanceStatus.present:
            by_type[training.tipo]["present"] += 1
        else:
            by_type[training.tipo]["absent"] += 1
        sessions_list.append(
            {
                "date": training.data.isoformat(),
                "tipo": training.tipo,
                "categories": [c.nome for c in training.categories],
                "status": status.value,
                "source": source.value,
                "change_count": change_count,
                "time_range": training.orario,
            }
        )

    presence_rate = kpi["present"] / kpi["sessions"] if kpi["sessions"] else 0

    monthly_list = [
        {"month": m, "present": d.get("present", 0), "absent": d.get("absent", 0)}
        for m, d in sorted(monthly.items())
    ]
    by_type_list = [
        {"type": t, "present": d.get("present", 0), "absent": d.get("absent", 0)}
        for t, d in sorted(by_type.items())
    ]

    return {
        "kpi": {
            "sessions": kpi["sessions"],
            "present": kpi["present"],
            "absent": kpi["absent"],
            "presence_rate": presence_rate,
        },
        "monthly": monthly_list,
        "by_type": by_type_list,
        "sessions": sessions_list,
    }
