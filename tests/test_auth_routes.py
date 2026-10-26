"""Regression coverage for the authentication routes on an isolated database."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "test-only-secret-key-at-least-32-bytes")
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("SNAPSHOT_DIR", str(tmp_path / "snapshots"))
    # Importing routers initializes their nft handlers. Never modify a real firewall.
    import subprocess
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: None)
    import app.main
    yield TestClient(app.main.app, follow_redirects=False)


def test_onboarding_login_and_protected_api(client):
    assert client.get("/").headers["location"] == "/login"
    assert client.get("/login").headers["location"] == "/onboarding"
    assert client.get("/onboarding").status_code == 200
    assert client.get("/healthz").json() == {"status": "ok"}
    response = client.get("/api/system/status")
    assert response.status_code == 401
    assert response.headers["content-type"].startswith("application/json")

    response = client.post("/onboarding", data={"username": "alice", "password": "correct-password"})
    assert response.status_code == 302
    assert client.post("/onboarding", data={"username": "bob", "password": "password"}).status_code == 400
    response = client.post("/login", data={"username": "alice", "password": "wrong"})
    assert "Invalid credentials" in response.text
    assert client.get("/api/system/status").status_code == 401
    response = client.post("/login", data={"username": "alice", "password": "correct-password"})
    assert response.status_code == 302
    assert "httponly" in response.headers["set-cookie"].lower()
    assert client.get("/").status_code == 200
    assert client.get("/api/system/status").status_code == 200
    client.get("/logout")
    assert client.get("/api/system/status").status_code == 401
