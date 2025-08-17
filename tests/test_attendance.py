import pytest
from datetime import date, timedelta

import models
from services.attendance_service import compute_status_for_athlete
from tests import factories


@pytest.mark.anyio
async def test_compute_status_for_athlete(db_session):
    atleta_role = factories.create_role(db_session, "atleta")
    categoria = factories.create_categoria(db_session, nome="Junior", eta_min=10, eta_max=18)
    athlete = factories.create_user(
        db_session, username="athlete", roles=[atleta_role], date_of_birth=date.today() - timedelta(days=15*365)
    )
    training = models.Allenamento(tipo="Test", data=date.today(), orario="08:00")
    training.categories.append(categoria)
    db_session.add(training)
    db_session.commit()

    status = compute_status_for_athlete(db_session, training.id, athlete.id)
    assert status == models.AttendanceStatus.maybe

    att = models.Attendance(training_id=training.id, athlete_id=athlete.id, status=models.AttendanceStatus.absent)
    db_session.add(att)
    db_session.commit()
    status = compute_status_for_athlete(db_session, training.id, athlete.id)
    assert status == models.AttendanceStatus.absent


@pytest.mark.anyio
async def test_athlete_toggle_limit(client, db_session):
    atleta_role = factories.create_role(db_session, "atleta")
    categoria = factories.create_categoria(db_session, nome="Junior", eta_min=10, eta_max=18)
    athlete = factories.create_user(
        db_session, username="athlete", roles=[atleta_role], date_of_birth=date.today() - timedelta(days=15*365)
    )
    training = models.Allenamento(tipo="Test", data=date.today() + timedelta(days=1), orario="08:00")
    training.categories.append(categoria)
    db_session.add(training)
    db_session.commit()

    await client.post("/login", data={"username": "athlete", "password": "password"}, follow_redirects=True)
    r = await client.post(f"/trainings/{training.id}/attendance/toggle", json={"new_status": "absent"})
    assert r.status_code == 200 and r.json()["change_count"] == 1
    r = await client.post(f"/trainings/{training.id}/attendance/toggle", json={"new_status": "present"})
    assert r.status_code == 200 and r.json()["change_count"] == 2
    r = await client.post(f"/trainings/{training.id}/attendance/toggle", json={"new_status": "absent"})
    assert r.status_code == 400


@pytest.mark.anyio
async def test_coach_can_set_status(client, db_session):
    coach_role = factories.create_role(db_session, "allenatore")
    atleta_role = factories.create_role(db_session, "atleta")
    categoria = factories.create_categoria(db_session, nome="Junior", eta_min=10, eta_max=18)
    coach = factories.create_user(db_session, username="coach", roles=[coach_role])
    athlete = factories.create_user(
        db_session, username="athlete", roles=[atleta_role], date_of_birth=date.today() - timedelta(days=15*365)
    )
    training = models.Allenamento(tipo="Test", data=date.today() + timedelta(days=1), orario="08:00")
    training.categories.append(categoria)
    db_session.add(training)
    db_session.commit()

    await client.post("/login", data={"username": "coach", "password": "password"}, follow_redirects=True)
    r = await client.post(
        f"/trainings/{training.id}/attendance/{athlete.id}",
        json={"status": "absent", "reason": "test"},
    )
    assert r.status_code == 200
    att = db_session.query(models.Attendance).filter_by(training_id=training.id, athlete_id=athlete.id).first()
    assert att.status == models.AttendanceStatus.absent
    log = db_session.query(models.AttendanceChangeLog).filter_by(attendance_id=att.id).first()
    assert log is not None and log.source == models.AttendanceSource.coach
