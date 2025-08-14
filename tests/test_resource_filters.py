import pytest

@pytest.mark.anyio
async def test_barche_search(client):
    r = await client.get("/risorse/barche?search=test")
    assert r.status_code == 200

@pytest.mark.anyio
async def test_pesi_categoria_filter(client):
    r = await client.get("/risorse/pesi?categoria=test")
    assert r.status_code == 200
