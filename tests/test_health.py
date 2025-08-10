import pytest


@pytest.mark.anyio
async def test_health_endpoints(client):
    res = await client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}

    res_head = await client.head("/health")
    assert res_head.status_code == 200
