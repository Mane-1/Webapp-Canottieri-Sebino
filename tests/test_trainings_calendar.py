import pytest

@pytest.mark.anyio
async def test_calendar_week_navigation(client):
    r = await client.get("/trainings/calendar")
    assert r.status_code == 200
    assert "Calendario" in r.text

@pytest.mark.anyio
async def test_create_training_ok(client):
    payload = {
        "tipo": "barca",
        "descrizione": "uscita prova",
        "date": "2025-08-20",
        "time_start": "09:00",
        "time_end": "10:30",
    }
    r = await client.post("/trainings", data=payload, follow_redirects=False)
    assert r.status_code in (303, 307)

@pytest.mark.anyio
async def test_calendar_filter_by_coach(client):
    r = await client.get("/trainings/calendar?coach_id=999")
    assert r.status_code == 200
