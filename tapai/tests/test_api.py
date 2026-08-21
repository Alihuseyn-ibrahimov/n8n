from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_search_keys_via_api():
    res = client.post("/api/search", json={"query": "açarımı tap", "mode": "fusion"})
    assert res.status_code == 200
    body = res.json()
    assert body["hits"]
    assert body["hits"][0]["category"] == "keys"
    assert body["target"]["material"] == "brass"


def test_unknown_query():
    res = client.post("/api/search", json={"query": "asdasd xyz"})
    assert res.status_code == 400
