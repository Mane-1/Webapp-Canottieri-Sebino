import pytest
import models
import security


async def _login(client, db_session):
    """Create an admin user and authenticate."""
    admin_role = models.Role(name="admin")
    db_session.add(admin_role)
    db_session.commit()
    user = models.User(
        username="gabriele",
        hashed_password=security.get_password_hash("manenti"),
        first_name="Test",
        last_name="User",
    )
    user.roles.append(admin_role)
    db_session.add(user)
    db_session.commit()
    await client.post(
        "/login",
        data={"username": "gabriele", "password": "manenti"},
        follow_redirects=True,
    )


@pytest.mark.anyio
async def test_barche_search(client, db_session):
    await _login(client, db_session)
    r = await client.get("/risorse/barche?search=test")
    assert r.status_code == 200


@pytest.mark.anyio
async def test_pesi_categoria_filter(client, db_session):
    await _login(client, db_session)
    r = await client.get("/risorse/pesi?categoria=test")
    assert r.status_code == 200
