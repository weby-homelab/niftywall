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


@pytest.mark.parametrize("handler_name", ["get_ruleset", "get_sets"])
def test_firewall_reads_do_not_block_event_loop(client, monkeypatch, handler_name):
    """A slow nft subprocess must not stop the worker's event loop."""
    import asyncio
    import threading

    from app import rules_router

    release = threading.Event()

    def slow_read():
        return {"timed_out": not release.wait(1)}

    monkeypatch.setattr(rules_router.nft, handler_name, slow_read)

    async def exercise():
        asyncio.get_running_loop().call_later(0.05, release.set)
        result = await getattr(rules_router, handler_name)(user="alice")
        assert result == {"timed_out": False}

    asyncio.run(exercise())
