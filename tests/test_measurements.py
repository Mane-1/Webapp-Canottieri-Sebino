import pytest
from datetime import date

import models
from tests import factories


@pytest.mark.anyio
async def test_measurements_insert_and_series(client, db_session):
    coach_role = factories.create_role(db_session, "allenatore")
    atleta_role = factories.create_role(db_session, "atleta")
    coach = factories.create_user(db_session, username="coach", roles=[coach_role])
    athlete = factories.create_user(db_session, username="athlete", roles=[atleta_role])

    await client.post("/login", data={"username": "coach", "password": "password"}, follow_redirects=True)
    await client.post(
        f"/athletes/{athlete.id}/measurements",
        json={"measured_at": date(2023,1,1).isoformat(), "weight_kg": 70},
    )
    await client.post(
        f"/athletes/{athlete.id}/measurements",
        json={"measured_at": date(2023,2,1).isoformat(), "weight_kg": 71},
    )

    r = await client.get(f"/api/athletes/{athlete.id}/measurements?metric=weight&year=2023")
    assert r.status_code == 200
    data = r.json()
    assert data["data"] == [70, 71]
    assert data["labels"][0] <= data["labels"][1]
