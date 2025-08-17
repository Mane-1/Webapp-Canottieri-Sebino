"""Helper functions for attendance management."""
from datetime import date
from typing import List
from sqlalchemy.orm import Session

import models


def get_roster_for_training(db: Session, training: models.Allenamento) -> List[models.User]:
    """Return athletes eligible for the given training.

    An athlete is part of the roster if their age at the date of the
    training falls within at least one of the training's categories.
    """
    roster: List[models.User] = []
    categories = list(training.categories)
    if not categories:
        return roster

    athletes = (
        db.query(models.User)
        .join(models.User.roles)
        .filter(models.Role.name == "atleta")
        .all()
    )
    training_date = training.data
    for athlete in athletes:
        if not athlete.date_of_birth:
            continue
        age = training_date.year - athlete.date_of_birth.year - (
            (training_date.month, training_date.day)
            < (athlete.date_of_birth.month, athlete.date_of_birth.day)
        )
        for cat in categories:
            if cat.eta_min <= age <= cat.eta_max:
                roster.append(athlete)
                break
    return roster


def compute_status_for_athlete(db: Session, training_id: int, athlete_id: int) -> models.AttendanceStatus:
    """Return the attendance status for the athlete in the training.

    If no record exists in ``Attendance`` the athlete is considered maybe
    (i.e. not yet confirmed) by default.
    """
    attendance = (
        db.query(models.Attendance)
        .filter_by(training_id=training_id, athlete_id=athlete_id)
        .first()
    )
    if attendance:
        return attendance.status
    return models.AttendanceStatus.maybe
