"""Routes for attendance management."""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import models
from schemas.attendance import (
    ToggleAttendanceIn,
    SetAttendanceIn,
    AttendanceBulkIn,
)
from database import get_db
from dependencies import get_current_user, get_current_admin_or_coach_user
from services.attendance_service import (
    get_roster_for_training,
    compute_status_for_athlete,
)
from utils import parse_orario

router = APIRouter(tags=["Presenze"])


@router.post("/trainings/{training_id}/attendance/toggle")
async def toggle_attendance(
    training_id: int,
    payload: ToggleAttendanceIn,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if not current_user.is_atleta:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only athletes can toggle attendance")
    training = db.get(models.Allenamento, training_id)
    if not training:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Training not found")
    start_dt, _ = parse_orario(training.data, training.orario)
    if datetime.utcnow() >= start_dt - timedelta(hours=3):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cambio limite superato")
    roster = get_roster_for_training(db, training)
    if current_user.id not in [a.id for a in roster]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not part of this training")
    desired_status = models.AttendanceStatus(payload.new_status)
    attendance = (
        db.query(models.Attendance)
        .filter_by(training_id=training_id, athlete_id=current_user.id)
        .first()
    )
    if attendance and attendance.status == desired_status:
        return {"status": attendance.status.value, "change_count": attendance.change_count}
    if attendance:
        old_status = attendance.status
        attendance.status = desired_status
        attendance.change_count += 1
        attendance.source = models.AttendanceSource.athlete
        attendance.last_changed_at = datetime.utcnow()
        log = models.AttendanceChangeLog(
            attendance=attendance,
            changed_by_user_id=current_user.id,
            old_status=old_status,
            new_status=desired_status,
            source=models.AttendanceSource.athlete,
        )
        db.add(log)
        db.commit()
        db.refresh(attendance)
        return {"status": attendance.status.value, "change_count": attendance.change_count}
    else:
        attendance = models.Attendance(
            training_id=training_id,
            athlete_id=current_user.id,
            status=desired_status,
            source=models.AttendanceSource.athlete,
            change_count=1,
            last_changed_at=datetime.utcnow(),
        )
        db.add(attendance)
        db.flush()
        log = models.AttendanceChangeLog(
            attendance_id=attendance.id,
            changed_by_user_id=current_user.id,
            old_status=models.AttendanceStatus.maybe,
            new_status=desired_status,
            source=models.AttendanceSource.athlete,
        )
        db.add(log)
        db.commit()
        db.refresh(attendance)
        return {"status": attendance.status.value, "change_count": attendance.change_count}


@router.get("/trainings/{training_id}/attendance")
async def list_attendance(
    training_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_or_coach_user),
):
    training = db.get(models.Allenamento, training_id)
    if not training:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Training not found")
    roster = get_roster_for_training(db, training)
    roster_ids = {a.id for a in roster}
    extra_attendances = (
        db.query(models.Attendance)
        .filter_by(training_id=training.id)
        .all()
    )
    for att in extra_attendances:
        if att.athlete_id not in roster_ids:
            roster.append(att.athlete)
            roster_ids.add(att.athlete_id)
    roster.sort(key=lambda a: ((a.last_name or '').lower(), (a.first_name or '').lower()))

    result = []
    for athlete in roster:
        status_val = compute_status_for_athlete(db, training.id, athlete.id)
        attendance = (
            db.query(models.Attendance)
            .filter_by(training_id=training.id, athlete_id=athlete.id)
            .first()
        )
        change_count = attendance.change_count if attendance else 0
        source = attendance.source.value if attendance else models.AttendanceSource.system.value
        result.append(
            {
                "athlete_id": athlete.id,
                "athlete_name": athlete.full_name,
                "status": status_val.value,
                "change_count": change_count,
                "source": source,
            }
        )
    return result


@router.post("/trainings/{training_id}/attendance/bulk")
async def bulk_set_attendance(
    training_id: int,
    payload: AttendanceBulkIn,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_or_coach_user),
):
    training = db.get(models.Allenamento, training_id)
    if not training:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Training not found")
    roster = {a.id for a in get_roster_for_training(db, training)}
    extra_ids = [
        att.athlete_id
        for att in db.query(models.Attendance).filter_by(training_id=training.id)
    ]
    roster.update(extra_ids)
    for item in payload.items:
        if item.athlete_id not in roster:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Athlete fuori roster",
            )
    reason = payload.reason
    results = []
    for item in payload.items:
        attendance = (
            db.query(models.Attendance)
            .filter_by(training_id=training_id, athlete_id=item.athlete_id)
            .first()
        )
        desired_status = models.AttendanceStatus(item.status)
        if attendance:
            old_status = attendance.status
            attendance.status = desired_status
            attendance.source = models.AttendanceSource.coach
            attendance.last_changed_at = datetime.utcnow()
        else:
            attendance = models.Attendance(
                training_id=training_id,
                athlete_id=item.athlete_id,
                status=desired_status,
                source=models.AttendanceSource.coach,
                last_changed_at=datetime.utcnow(),
            )
            db.add(attendance)
            old_status = models.AttendanceStatus.maybe
            db.flush()
        log = models.AttendanceChangeLog(
            attendance_id=attendance.id,
            changed_by_user_id=current_user.id,
            old_status=old_status,
            new_status=desired_status,
            source=models.AttendanceSource.coach,
            reason=reason,
        )
        db.add(log)
        results.append({"athlete_id": item.athlete_id, "status": desired_status.value})
    db.commit()
    return {"updated": results}


@router.post("/trainings/{training_id}/attendance/{athlete_id}")
async def set_attendance(
    training_id: int,
    athlete_id: int,
    payload: SetAttendanceIn,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_or_coach_user),
):
    training = db.get(models.Allenamento, training_id)
    if not training:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Training not found")
    desired_status = models.AttendanceStatus(payload.status)
    reason = payload.reason
    attendance = (
        db.query(models.Attendance)
        .filter_by(training_id=training_id, athlete_id=athlete_id)
        .first()
    )
    if attendance:
        old_status = attendance.status
        attendance.status = desired_status
        attendance.source = models.AttendanceSource.coach
        attendance.last_changed_at = datetime.utcnow()
    else:
        attendance = models.Attendance(
            training_id=training_id,
            athlete_id=athlete_id,
            status=desired_status,
            source=models.AttendanceSource.coach,
            last_changed_at=datetime.utcnow(),
        )
        db.add(attendance)
        old_status = models.AttendanceStatus.maybe
        db.flush()
    log = models.AttendanceChangeLog(
        attendance_id=attendance.id,
        changed_by_user_id=current_user.id,
        old_status=old_status,
        new_status=desired_status,
        source=models.AttendanceSource.coach,
        reason=reason,
    )
    db.add(log)
    db.commit()
    db.refresh(attendance)
    return {"status": attendance.status.value, "change_count": attendance.change_count}


@router.post("/trainings/{training_id}/categories/{category_name}")
async def toggle_training_category(
    training_id: int,
    category_name: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_or_coach_user),
):
    training = db.get(models.Allenamento, training_id)
    if not training:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Training not found")
    category = (
        db.query(models.Categoria).filter(models.Categoria.nome == category_name).first()
    )
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    if category in training.categories:
        training.categories.remove(category)
        assigned = False
        # remove attendance records for athletes no longer matching any category
        remaining_ids = {a.id for a in get_roster_for_training(db, training)}
        (
            db.query(models.Attendance)
            .filter(
                models.Attendance.training_id == training_id,
                ~models.Attendance.athlete_id.in_(remaining_ids),
            )
            .delete(synchronize_session=False)
        )
    else:
        training.categories.append(category)
        assigned = True
    db.commit()
    return {"assigned": assigned}
