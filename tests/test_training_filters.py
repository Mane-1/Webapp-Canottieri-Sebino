import pytest
from datetime import date, timedelta
import models
from tests.factories import create_categoria, create_admin_user


@pytest.mark.anyio
async def test_category_filter_without_dates(client, db_session):
    cat1 = create_categoria(db_session, nome="Cat1")
    cat2 = create_categoria(db_session, nome="Cat2")
    admin = create_admin_user(db_session)
    t1 = models.Allenamento(
        tipo="Barca",
        descrizione="T1",
        data=date.today() + timedelta(days=1),
        orario="08:00",
        categories=[cat1],
    )
    t2 = models.Allenamento(
        tipo="Barca",
        descrizione="T2",
        data=date.today() + timedelta(days=1),
        orario="09:00",
        categories=[cat2],
    )
    db_session.add_all([t1, t2])
    db_session.commit()

    await client.post(
        "/login",
        data={"username": admin.username, "password": "password"},
        follow_redirects=True,
    )

    res = await client.get(f"/allenamenti?category={cat1.nome}")
    assert res.status_code == 200
    text = res.text
    assert "T1" in text
    assert "T2" not in text
