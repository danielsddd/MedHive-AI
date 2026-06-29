"""
Endpoint smoke tests via FastAPI's ASGI test client. /healthz must always return the
4-key shape (db/redis/embedding_service/gateway) without throwing, even with no database;
/auth/me must 401 with the stable jwt_invalid code when no token is sent and 200 with the
dev user when a bearer token is present in dev mode.
"""
from fastapi.testclient import TestClient

import main

client = TestClient(main.app)


def test_healthz_shape():
    r = client.get("/healthz")
    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"db", "redis", "embedding_service", "gateway"}
    assert body["embedding_service"] == "up"
    assert body["gateway"] == "up"


def test_me_requires_token():
    r = client.get("/auth/me")
    assert r.status_code == 401
    assert r.json()["code"] == "jwt_invalid"


def test_me_dev_mode_returns_user():
    r = client.get("/auth/me", headers={"Authorization": "Bearer devtoken"})
    assert r.status_code == 200
    assert r.json()["role"] == "researcher"
