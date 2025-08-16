import pytest
from datetime import date

import models
from main import app
from dependencies import get_current_admin_or_coach_user
from tests import factories


@pytest.mark.anyio
async def test_stats_filtering(client, db_session):
    admin_role = factories.create_role(db_session, "admin")
    coach_role = factories.create_role(db_session, "allenatore")
    admin = factories.create_user(db_session, username="admin", roles=[admin_role])
    coach = factories.create_user(db_session, username="coach", roles=[coach_role])
    year = date.today().year
    july = date(year, 7, 1)
    august = date(year, 8, 1)
    t1 = models.Turno(data=july, fascia_oraria="Mattina", user_id=coach.id)
    t2 = models.Turno(data=july.replace(day=2), fascia_oraria="Sera")
    t3 = models.Turno(data=august, fascia_oraria="Mattina", user_id=coach.id)
    db_session.add_all([t1, t2, t3])
    db_session.commit()
    app.dependency_overrides[get_current_admin_or_coach_user] = lambda: admin
    r = await client.get(f"/turni/statistiche?year={year}&month=7")
    assert r.status_code == 200
    assert "Coperti 1" in r.text
    assert "Scoperti 1" in r.text
