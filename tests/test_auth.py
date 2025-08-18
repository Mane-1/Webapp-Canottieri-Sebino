import pytest
import models, security


@pytest.mark.anyio
async def test_login_page_renders(client):
    res = await client.get("/login")
    assert res.status_code == 200
    assert "Login" in res.text


@pytest.mark.anyio
async def test_login_requires_fields(client):
    res = await client.post("/login", data={"username": "", "password": ""})
    assert res.status_code == 400
    assert "Compila tutti i campi" in res.text


@pytest.mark.anyio
async def test_account_lockout_after_failed_attempts(client, db_session):
    user = models.User(
        username="test", hashed_password=security.get_password_hash("secret"), first_name="T", last_name="U"
    )
    db_session.add(user)
    db_session.commit()

    for i in range(10):
        res = await client.post("/login", data={"username": "test", "password": "wrong"})
        if i < 9:
            assert res.status_code == 401
            assert "Username o password non validi" in res.text
        else:
            assert res.status_code == 403
            assert "Account sospeso" in res.text

    # even with correct password after lockout
    res = await client.post("/login", data={"username": "test", "password": "secret"})
    assert res.status_code == 403
    assert "Account sospeso" in res.text

    # simulate admin reset
    user.hashed_password = security.get_password_hash("new")
    user.failed_login_attempts = 0
    user.is_suspended = False
    db_session.commit()

    res = await client.post("/login", data={"username": "test", "password": "new"})
    assert res.status_code == 303
