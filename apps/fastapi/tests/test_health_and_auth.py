"""
Endpoint smoke tests via FastAPI's ASGI test client. /healthz must always return the
4-key shape (db/redis/embedding_service/gateway) without throwing, even with no database.
/auth/me must 401 with the stable jwt_invalid code when no token is sent, and must 401
when Supabase rejects the token (with placeholder CI credentials there is no real Supabase
project to validate against, so any token is correctly rejected — no real network call is
made or needed). A genuine 200 path is covered by integration tests against a real
Supabase project, not this unit suite.
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


def test_me_rejects_invalid_token():
    """With placeholder CI credentials (no real Supabase project), any bearer token
    fails validation and the endpoint must fail closed with jwt_invalid — never a 500
    or a leaked stack trace."""
    r = client.get("/auth/me", headers={"Authorization": "Bearer not-a-real-jwt"})
    assert r.status_code == 401
    assert r.json()["code"] == "jwt_invalid"