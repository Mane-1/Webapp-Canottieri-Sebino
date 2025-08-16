import pytest
from datetime import date

import models
from main import app
from dependencies import get_current_admin_or_coach_user
from tests import factories
from utils import MONTH_NAMES


@pytest.mark.anyio
async def test_export_turni(client, db_session):
    role = factories.create_role(db_session, "allenatore")
    coach = factories.create_user(db_session, roles=[role])
    today = date.today()
    current_turno = models.Turno(data=today, fascia_oraria="8:00-10:00", user_id=coach.id)
    # turno from previous month shouldn't appear in export
    if today.month == 1:
        prev_month_date = date(today.year - 1, 12, 1)
    else:
        prev_month_date = date(today.year, today.month - 1, 1)
    other_turno = models.Turno(data=prev_month_date, fascia_oraria="Sera")
    db_session.add_all([current_turno, other_turno])
    db_session.commit()
    app.dependency_overrides[get_current_admin_or_coach_user] = lambda: coach
    r_csv = await client.get("/turni/export/csv")
    assert r_csv.status_code == 200
    title = f"Turni aperture Canottieri {MONTH_NAMES[today.month]} {today.year}"
    assert title in r_csv.text.splitlines()[0]
    assert str(prev_month_date) not in r_csv.text
    assert title.replace(" ", "%20") in r_csv.headers["content-disposition"]
    r_xlsx = await client.get("/turni/export/excel")
    assert r_xlsx.status_code == 200
    assert title.replace(" ", "%20") in r_xlsx.headers["content-disposition"]


@pytest.mark.anyio
async def test_availability_overwrite_and_api(client, db_session):
    coach_role = factories.create_role(db_session, "allenatore")
    coach = factories.create_user(db_session, roles=[coach_role])
    # create two turni for next month
    today = date.today().replace(day=1)
    if today.month == 12:
        next_month = date(today.year + 1, 1, 1)
    else:
        next_month = date(today.year, today.month + 1, 1)
    t1 = models.Turno(data=next_month, fascia_oraria="Mattina")
    t2 = models.Turno(data=next_month, fascia_oraria="Sera")
    db_session.add_all([t1, t2])
    db_session.commit()
    app.dependency_overrides[get_current_admin_or_coach_user] = lambda: coach
    r = await client.post("/turni/disponibilita", data={"turno_ids": str(t1.id)}, follow_redirects=False)
    assert r.status_code in (303, 307)
    assert (
        db_session.query(models.TrainerAvailability)
        .filter_by(user_id=coach.id, turno_id=t1.id)
        .count()
        == 1
    )
    r2 = await client.post("/turni/disponibilita", data={"turno_ids": str(t2.id)}, follow_redirects=False)
    assert r2.status_code in (303, 307)
    assert (
        db_session.query(models.TrainerAvailability)
        .filter_by(user_id=coach.id, turno_id=t1.id)
        .count()
        == 0
    )
    assert (
        db_session.query(models.TrainerAvailability)
        .filter_by(user_id=coach.id, turno_id=t2.id)
        .count()
        == 1
    )
    events = await client.get("/api/turni")
    assert events.status_code == 200
    data = events.json()
    event = next(e for e in data if e["id"] == t2.id)
    assert coach.id in event["extendedProps"]["available_ids"]
