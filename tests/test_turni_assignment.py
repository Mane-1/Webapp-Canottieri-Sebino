import pytest
from datetime import date

import models
from main import app
from dependencies import get_current_admin_user
from tests import factories


@pytest.mark.anyio
async def test_assign_turno_redirect(client, db_session):
    admin_role = factories.create_role(db_session, "admin")
    coach_role = factories.create_role(db_session, "allenatore")
    admin = factories.create_user(db_session, username="admin", roles=[admin_role])
    coach = factories.create_user(db_session, username="coach", roles=[coach_role])
    turno = models.Turno(data=date.today(), fascia_oraria="Mattina")
    db_session.add(turno)
    db_session.commit()
    app.dependency_overrides[get_current_admin_user] = lambda: admin
    resp = await client.post(
        "/turni/assegna",
        data={"turno_id": turno.id, "user_id": coach.id, "week_offset": 0},
        follow_redirects=False,
    )
    assert resp.status_code == 303
    db_session.refresh(turno)
    assert turno.user_id == coach.id


@pytest.mark.anyio
async def test_quick_assignment(client, db_session):
    admin_role = factories.create_role(db_session, "admin")
    coach_role = factories.create_role(db_session, "allenatore")
    admin = factories.create_user(db_session, username="admin", roles=[admin_role])
    coach = factories.create_user(db_session, username="coach", roles=[coach_role])
    t1 = models.Turno(data=date.today(), fascia_oraria="Mattina")
    t2 = models.Turno(data=date.today(), fascia_oraria="Sera")
    db_session.add_all([t1, t2])
    db_session.commit()
    app.dependency_overrides[get_current_admin_user] = lambda: admin
    resp = await client.post(
        "/turni/assegna_rapida",
        data={"user_id": str(coach.id), "turno_ids": [str(t1.id), str(t2.id)], "week_offset": "0"},
        follow_redirects=False,
    )
    assert resp.status_code == 303
    db_session.refresh(t1)
    db_session.refresh(t2)
    assert t1.user_id == coach.id
    assert t2.user_id == coach.id

