# tests/test_web_server.py
from fastapi.testclient import TestClient
from aero_code.web.server import create_app
from aero_code.state import ProofLoopEventBus


def test_dashboard_index_and_status():
    bus = ProofLoopEventBus()
    app = create_app(event_bus=bus)
    client = TestClient(app)
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Aero-Code" in resp.text

    status_resp = client.get("/api/status")
    assert status_resp.status_code == 200
    assert "status" in status_resp.json()


def test_run_trigger_endpoint():
    bus = ProofLoopEventBus()
    app = create_app(event_bus=bus)
    client = TestClient(app)

    # Trigger a run on demo issue
    payload = {
        "issue_id": "TEST-WEB",
        "title": "Web Test",
        "description": "Testing web trigger",
        "traceback": "",
        "target_package": "test-pkg",
        "package_version": "1.0.0",
        "mode": "demo",
    }
    resp = client.post("/api/run", json=payload)
    assert resp.status_code in (200, 202)
    assert "run_id" in resp.json()
