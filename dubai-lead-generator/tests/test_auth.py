"""
Unit and API integration tests for authentication and JWT security.
"""

import pytest
from datetime import timedelta
from fastapi.testclient import TestClient

from app.main import app
from app.utils.auth import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)
from app.config import settings


@pytest.fixture
def client():
    return TestClient(app)


def test_password_hashing():
    raw = "SuperSecretPassword123!"
    h = hash_password(raw)
    assert h != raw
    assert verify_password(raw, h) is True
    assert verify_password("WrongPassword", h) is False


def test_jwt_token_lifecycle():
    data = {"sub": "admin@litsa.io", "role": "admin"}
    token = create_access_token(data, expires_delta=timedelta(minutes=5))
    assert isinstance(token, str)
    decoded = decode_access_token(token)
    assert decoded["sub"] == "admin@litsa.io"
    assert decoded["role"] == "admin"


def test_login_flow(client):
    email = settings.admin_email or "admin@litsa.io"
    default_pwd = settings.admin_default_password or "Admin@Litsa2026!"

    # Valid login
    res = client.post("/api/v1/auth/login", json={"email": email, "password": default_pwd})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    # Test authenticated /me
    token = data["access_token"]
    me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["user"]["email"] == email.lower()


def test_invalid_login(client):
    res = client.post("/api/v1/auth/login", json={"email": "wrong@litsa.io", "password": "WrongPassword"})
    assert res.status_code == 401
