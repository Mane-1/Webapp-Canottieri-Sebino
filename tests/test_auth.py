import pytest


@pytest.mark.anyio
async def test_login_page_renders(client):
    res = await client.get("/login")
    assert res.status_code == 200
    assert "Login" in res.text
