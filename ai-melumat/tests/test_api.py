from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_and_listings():
    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.json()["service"] == "ai-melumat"

    data = client.get("/api/listings").json()
    assert data["source"] in {"file", "fixture"}
    assert len(data["elanlar"]) == 12
    assert data["statistika"]["en_ucuz"] == 24800


def test_chat_grounding():
    client.get("/api/listings")
    res = client.post("/api/chat", json={"query": "ən ucuz hansıdır?"})
    body = res.json()
    assert res.status_code == 200
    assert "Lada Vesta" in body["text"]
    assert body["elanlar"][0]["ad"] == "Lada Vesta"


def test_ui_served():
    page = client.get("/")
    assert page.status_code == 200
    assert "Məlumatçı" in page.text
    css = client.get("/static/styles.css")
    assert css.status_code == 200
