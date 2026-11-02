import asyncio
import json
import threading
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from aero_code.schemas.report import EvidenceReport, VerificationVerdict
from aero_code.state import ProofLoopEventBus
from aero_code.web.server import create_app


class RecordingOrchestrator:
    def __init__(self, bus, failure=False):
        self.bus = bus
        self.failure = failure
        self.repositories = []
        self.entered = threading.Event()
        self.release = None

    def run(self, issue, repo_dir):
        self.repositories.append(Path(repo_dir))
        self.entered.set()
        if self.release is not None:
            assert self.release.wait(5)
        if self.failure:
            raise RuntimeError("sandbox could not start")
        self.bus.publish("PHASE_CHANGE", {"phase": "INTAKE"})
        return EvidenceReport(
            run_id="proof-run", verdict=VerificationVerdict.INCONCLUSIVE
        )


@pytest.mark.parametrize("case", [
    "pydantic_v2_migration", "requests_timeout_kwarg", "paypal_webhook_signature",
])
def test_presets_execute_their_own_repository(case):
    bus = ProofLoopEventBus()
    orchestrator = RecordingOrchestrator(bus)
    client = TestClient(create_app(bus, orchestrator))
    response = client.post("/api/run", json={"case_id": case})
    assert response.status_code == 202
    assert orchestrator.repositories[0].parent.name == case
    status = client.get("/api/status").json()
    assert status["last_report"]["run_id"] == response.json()["run_id"]
    assert status["status"] == "idle"


@pytest.mark.parametrize("payload,status", [
    ({"case_id": "missing-case"}, 404),
    ({"repo_dir": "Z:\\aero-code-missing-repo"}, 400),
    ({"mode": "invalid"}, 422),
    ({"title": "   "}, 422),
])
def test_invalid_run_requests_are_rejected(payload, status):
    bus = ProofLoopEventBus()
    orchestrator = RecordingOrchestrator(bus)
    client = TestClient(create_app(bus, orchestrator))
    response = client.post("/api/run", json=payload)
    assert response.status_code == status
    assert not orchestrator.repositories


def test_background_failure_is_visible_and_next_run_can_start(caplog):
    bus = ProofLoopEventBus()
    orchestrator = RecordingOrchestrator(bus, failure=True)
    client = TestClient(create_app(bus, orchestrator), raise_server_exceptions=False)
    assert client.post("/api/run", json={}).status_code == 202
    status = client.get("/api/status").json()
    assert status["status"] == "idle"
    assert status["last_error"] == "sandbox could not start"
    assert status["last_verdict"] == "FAILED"
    assert status["events"][-1]["event_type"] == "RUN_FAILED"
    assert "sandbox could not start" in caplog.text
    orchestrator.failure = False
    assert client.post("/api/run", json={}).status_code == 202
    recovered = client.get("/api/status").json()
    assert recovered["last_error"] is None
    assert recovered["last_report"]["verdict"] == "INCONCLUSIVE"


def test_overlapping_run_is_rejected_before_second_execution():
    bus = ProofLoopEventBus()
    orchestrator = RecordingOrchestrator(bus)
    orchestrator.release = threading.Event()
    client = TestClient(create_app(bus, orchestrator))
    responses = []
    worker = threading.Thread(target=lambda: responses.append(client.post("/api/run", json={})))
    worker.start()
    try:
        assert orchestrator.entered.wait(2)
        assert client.get("/api/status").json()["status"] == "running"
        assert client.post("/api/run", json={}).status_code == 409
    finally:
        orchestrator.release.set()
        worker.join(5)
    assert not worker.is_alive()
    assert len(orchestrator.repositories) == 1
    assert responses[0].status_code == 202


def test_sse_receives_worker_thread_events_and_replays_snapshot():
    async def scenario():
        bus = ProofLoopEventBus()
        app = create_app(bus)
        endpoint = next(route.endpoint for route in app.routes if route.path == "/api/stream")

        class Request:
            async def is_disconnected(self):
                return False

        response = await endpoint(Request())
        iterator = response.body_iterator
        assert "event: connected" in await anext(iterator)
        snapshot = await anext(iterator)
        assert "event: snapshot" in snapshot
        next_event = asyncio.create_task(anext(iterator))
        await asyncio.sleep(0)
        await asyncio.to_thread(bus.publish, "PATCH_GENERATED", {"patch": {"diffs": []}})
        data = await asyncio.wait_for(next_event, 1)
        assert "event: proofloop" in data
        payload = json.loads(data.split("data: ", 1)[1])
        assert payload["event_type"] == "PATCH_GENERATED"
        assert payload["sequence"] > 0
        await iterator.aclose()
        reconnect = (await endpoint(Request())).body_iterator
        await anext(reconnect)
        replay = await anext(reconnect)
        assert "PATCH_GENERATED" in replay
        await reconnect.aclose()

    asyncio.run(scenario())


def test_orchestrator_completion_is_not_published_twice():
    bus = ProofLoopEventBus()

    class CompletingOrchestrator(RecordingOrchestrator):
        def run(self, issue, repo_dir):
            report = super().run(issue, repo_dir)
            self.bus.publish("RUN_COMPLETE", {
                "verdict": report.verdict.value,
                "report": report.model_dump(mode="json"),
            })
            return report

    client = TestClient(create_app(bus, CompletingOrchestrator(bus)))
    response = client.post("/api/run", json={})
    events = client.get("/api/status").json()["events"]
    completions = [event for event in events if event["event_type"] == "RUN_COMPLETE"]
    assert len(completions) == 1
    assert completions[0]["payload"]["report"]["run_id"] == response.json()["run_id"]
