import csv
from datetime import date
import pytest
import models
from tests.factories import create_role, create_user, create_admin_user, create_categoria


@pytest.mark.anyio
async def test_access_control_requires_staff(client, db_session):
    role = create_role(db_session, "atleta")
    user = create_user(db_session, roles=[role])
    await client.post("/login", data={"username": user.username, "password": "password"}, follow_redirects=True)
    assert (await client.get("/athletes")).status_code == 403
    assert (await client.get("/athletes/1")).status_code == 403
    assert (await client.get("/trainings/stats")).status_code == 403


@pytest.mark.anyio
async def test_athlete_attendance_stats_default_present(client, db_session):
    cat = create_categoria(db_session, nome="Junior", eta_min=0, eta_max=30)
    role_a = create_role(db_session, "atleta")
    athlete = create_user(db_session, username="ath", roles=[role_a], date_of_birth=date(2005,1,1))
    role_c = create_role(db_session, "allenatore")
    coach = create_user(db_session, username="coach", roles=[role_c])
    training = models.Allenamento(tipo="Barca", data=date(2025,1,10), orario="08:00-10:00", categories=[cat], coaches=[coach])
    db_session.add(training)
    db_session.commit()
    await client.post("/login", data={"username": coach.username, "password": "password"}, follow_redirects=True)
    resp = await client.get(f"/api/athletes/{athlete.id}/attendance_stats", params={"year": 2025})
    assert resp.status_code == 200
    data = resp.json()
    assert data["kpi"]["sessions"] == 1
    assert data["kpi"]["present"] == 0
    assert data["kpi"]["absent"] == 1


@pytest.mark.anyio
async def test_trainings_stats_hours_and_monthly(client, db_session):
    cat = create_categoria(db_session, nome="Junior", eta_min=0, eta_max=30)
    role_a = create_role(db_session, "atleta")
    athlete = create_user(db_session, roles=[role_a], date_of_birth=date(2005,1,1))
    role_c = create_role(db_session, "allenatore")
    coach = create_user(db_session, username="coach2", roles=[role_c])
    training = models.Allenamento(tipo="Barca", data=date(2025,2,10), orario="08:00-10:00", categories=[cat], coaches=[coach])
    db_session.add(training)
    db_session.commit()
    attendance = models.Attendance(training_id=training.id, athlete_id=athlete.id, status=models.AttendanceStatus.absent)
    db_session.add(attendance)
    db_session.commit()
    await client.post("/login", data={"username": coach.username, "password": "password"}, follow_redirects=True)
    resp = await client.get("/api/trainings/stats", params={"year": 2025})
    assert resp.status_code == 200
    data = resp.json()
    assert data["kpi"]["trainings"] == 1
    assert data["kpi"]["total_hours"] == 2.0
    assert data["kpi"]["absent"] == 1
    assert data["monthly"][0]["month"] == 2


@pytest.mark.anyio
async def test_csv_endpoints(client, db_session):
    cat = create_categoria(db_session, nome="Junior", eta_min=0, eta_max=30)
    role_a = create_role(db_session, "atleta")
    athlete = create_user(db_session, roles=[role_a], date_of_birth=date(2005,1,1))
    role_c = create_role(db_session, "allenatore")
    coach = create_user(db_session, username="coach3", roles=[role_c])
    training = models.Allenamento(tipo="Barca", data=date(2025,3,10), orario="08:00-10:00", categories=[cat], coaches=[coach])
    db_session.add(training)
    db_session.commit()
    await client.post("/login", data={"username": coach.username, "password": "password"}, follow_redirects=True)
    resp1 = await client.get(f"/api/athletes/{athlete.id}/attendance.csv", params={"year": 2025})
    assert resp1.headers["content-type"].startswith("text/csv")
    resp2 = await client.get("/api/trainings/stats.csv", params={"year": 2025})
    assert resp2.headers["content-type"].startswith("text/csv")
