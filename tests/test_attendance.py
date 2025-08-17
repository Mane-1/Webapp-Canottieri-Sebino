import pytest
from datetime import date, timedelta, datetime

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
async def test_athlete_toggle_time_window(client, db_session):
    atleta_role = factories.create_role(db_session, "atleta")
    categoria = factories.create_categoria(db_session, nome="Junior", eta_min=10, eta_max=18)
    athlete = factories.create_user(
        db_session, username="athlete", roles=[atleta_role], date_of_birth=date.today() - timedelta(days=15*365)
    )
    start_dt = datetime.utcnow() + timedelta(hours=5)
    training = models.Allenamento(tipo="Test", data=start_dt.date(), orario=start_dt.strftime("%H:%M"))
    training.categories.append(categoria)
    db_session.add(training)
    db_session.commit()

    await client.post("/login", data={"username": "athlete", "password": "password"}, follow_redirects=True)
    for _ in range(4):
        r = await client.post(f"/trainings/{training.id}/attendance/toggle", json={"new_status": "absent"})
        assert r.status_code == 200
        r = await client.post(f"/trainings/{training.id}/attendance/toggle", json={"new_status": "present"})
        assert r.status_code == 200

    # move training within 2 hours
    new_start = datetime.utcnow() + timedelta(hours=2)
    training.data = new_start.date()
    training.orario = new_start.strftime("%H:%M")
    db_session.commit()
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


@pytest.mark.anyio
async def test_bulk_update_allows_extra_attendee(client, db_session):
    coach_role = factories.create_role(db_session, "allenatore")
    atleta_role = factories.create_role(db_session, "atleta")
    coach = factories.create_user(db_session, username="coach2", roles=[coach_role])
    athlete = factories.create_user(
        db_session, username="athlete2", roles=[atleta_role], date_of_birth=date.today() - timedelta(days=15*365)
    )
    training = models.Allenamento(tipo="Test", data=date.today() + timedelta(days=1), orario="08:00")
    db_session.add(training)
    db_session.commit()

    await client.post("/login", data={"username": "coach2", "password": "password"}, follow_redirects=True)
    r = await client.post(
        f"/trainings/{training.id}/attendance/{athlete.id}",
        json={"status": "maybe"},
    )
    assert r.status_code == 200
    r = await client.post(
        f"/trainings/{training.id}/attendance/bulk",
        json={"items": [{"athlete_id": athlete.id, "status": "present"}]},
    )
    assert r.status_code == 200
    att = db_session.query(models.Attendance).filter_by(training_id=training.id, athlete_id=athlete.id).first()
    assert att.status == models.AttendanceStatus.present


@pytest.mark.anyio
async def test_attendance_list_sorted_with_manual_add(client, db_session):
    coach_role = factories.create_role(db_session, "allenatore")
    atleta_role = factories.create_role(db_session, "atleta")
    coach = factories.create_user(db_session, username="coach_sort", roles=[coach_role])
    cat = factories.create_categoria(db_session, nome="Junior", eta_min=10, eta_max=18)
    athlete_v = factories.create_user(
        db_session,
        username="athlete_v",
        roles=[atleta_role],
        first_name="Mario",
        last_name="Verdi",
        date_of_birth=date.today() - timedelta(days=15 * 365),
    )
    athlete_z = factories.create_user(
        db_session,
        username="athlete_z",
        roles=[atleta_role],
        first_name="Luca",
        last_name="Zappa",
        date_of_birth=date.today() - timedelta(days=16 * 365),
    )
    athlete_b = factories.create_user(
        db_session,
        username="athlete_b",
        roles=[atleta_role],
        first_name="Anna",
        last_name="Bianchi",
        date_of_birth=date.today() - timedelta(days=25 * 365),
    )
    training = models.Allenamento(tipo="Test", data=date.today() + timedelta(days=1), orario="08:00")
    training.categories.append(cat)
    db_session.add(training)
    db_session.commit()

    att = models.Attendance(training_id=training.id, athlete_id=athlete_b.id, status=models.AttendanceStatus.maybe)
    db_session.add(att)
    db_session.commit()

    await client.post("/login", data={"username": "coach_sort", "password": "password"}, follow_redirects=True)
    r = await client.get(f"/trainings/{training.id}/attendance")
    assert r.status_code == 200
    data = r.json()
    last_names = [row["athlete_name"].rsplit(" ", 1)[-1] for row in data]
    assert last_names == ["Bianchi", "Verdi", "Zappa"]


@pytest.mark.anyio
async def test_toggle_training_category(client, db_session):
    coach_role = factories.create_role(db_session, "allenatore")
    coach = factories.create_user(db_session, username="coach3", roles=[coach_role])
    cat = factories.create_categoria(db_session, nome="Junior", eta_min=10, eta_max=18)
    training = models.Allenamento(tipo="Test", data=date.today() + timedelta(days=1), orario="08:00")
    db_session.add(training)
    db_session.commit()
    athlete = factories.create_user(db_session, username="ath1", date_of_birth=date.today() - timedelta(days=365*15))
    attend = models.Attendance(training_id=training.id, athlete_id=athlete.id, status=models.AttendanceStatus.present)
    db_session.add(attend)
    db_session.commit()

    await client.post("/login", data={"username": "coach3", "password": "password"}, follow_redirects=True)
    r = await client.post(f"/trainings/{training.id}/categories/{cat.nome}")
    assert r.status_code == 200
    db_session.refresh(training)
    assert cat in training.categories
    # removing category should also drop attendance for its athletes
    r = await client.post(f"/trainings/{training.id}/categories/{cat.nome}")
    assert r.status_code == 200
    db_session.refresh(training)
    assert cat not in training.categories
    assert (
        db_session.query(models.Attendance)
        .filter_by(training_id=training.id, athlete_id=athlete.id)
        .count()
        == 0
    )


@pytest.mark.anyio
async def test_api_categories(client, db_session):
    coach_role = factories.create_role(db_session, "allenatore")
    coach = factories.create_user(db_session, username="coach_cat", roles=[coach_role])
    factories.create_categoria(db_session, nome="Junior", macro_group="Over 14", ordine=1)
    factories.create_categoria(db_session, nome="Master", macro_group="Master", ordine=2)
    await client.post(
        "/login",
        data={"username": "coach_cat", "password": "password"},
        follow_redirects=True,
    )
    resp = await client.get("/api/categories")
    assert resp.status_code == 200
    data = resp.json()
    assert any(c["name"] == "Junior" and c["group"] == "Over 14" for c in data)
    assert any(c["name"] == "Master" and c["group"] == "Master" for c in data)


@pytest.mark.anyio
async def test_update_training_categories(client, db_session):
    coach_role = factories.create_role(db_session, "allenatore")
    coach = factories.create_user(db_session, username="coach_upd", roles=[coach_role])
    cat1 = factories.create_categoria(db_session, nome="Junior", macro_group="Over 14", ordine=1)
    cat2 = factories.create_categoria(db_session, nome="Senior", macro_group="Over 14", ordine=2)
    training = models.Allenamento(tipo="Test", data=date.today() + timedelta(days=1), orario="08:00")
    training.categories.append(cat1)
    training.coaches.append(coach)
    db_session.add(training)
    db_session.commit()

    await client.post("/login", data={"username": "coach_upd", "password": "password"}, follow_redirects=True)
    new_date = date.today() + timedelta(days=2)
    r = await client.post(
        f"/allenamenti/{training.id}/modifica",
        data={
            "tipo": "Updated",
            "descrizione": "desc",
            "data": new_date.isoformat(),
            "orario": "09:00",
            "category_names": [cat1.nome, cat2.nome],
            "coach_ids": [str(coach.id)],
        },
        follow_redirects=False,
    )
    assert r.status_code == 303
    db_session.refresh(training)
    assert training.tipo == "Updated"
    assert training.data == new_date
    assert cat2 in training.categories
