from http import HTTPStatus

from fastapi import Response

from app.api.routes import auth
from app.core.config import Settings
from app.schemas.user import UserCreate


def test_register_and_me(client):
    payload = {
        "email": "user@example.com",
        "password": "verysecure",
        "timezone": "America/Argentina/Buenos_Aires",
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == HTTPStatus.CREATED
    data = response.json()
    assert data["email"] == payload["email"]

    me_resp = client.get("/auth/me")
    assert me_resp.status_code == HTTPStatus.OK
    me = me_resp.json()
    assert me["email"] == payload["email"]


def test_login_sets_cookie(client):
    # register first
    client.post(
        "/auth/register",
        json={
            "email": "login@example.com",
            "password": "verysecure",
            "timezone": "UTC",
        },
    )
    client.cookies.clear()

    response = client.post(
        "/auth/login",
        json={"email": "login@example.com", "password": "verysecure"},
    )
    assert response.status_code == HTTPStatus.OK
    assert "access_token" in client.cookies


def test_cookie_secure_can_be_disabled_behind_internal_http(monkeypatch):
    internal_http_settings = Settings(
        DATABASE_URL="sqlite:///test.db",
        JWT_SECRET="test-secret",
        APP_ENV="production",
        COOKIE_SECURE=False,
    )
    monkeypatch.setattr(auth, "settings", internal_http_settings)
    response = Response()

    auth._set_auth_cookie(response, "token", 60)

    assert "Secure" not in response.headers["set-cookie"]
