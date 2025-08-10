import pytest


@pytest.mark.anyio
async def test_base_template_without_user(client):
    res = await client.get("/login")
    assert res.status_code == 200
    assert "id=\"adminMenu\"" not in res.text
