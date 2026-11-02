import socket
import threading
import time

import pytest

from aero_code.state import ProofLoopEventBus, ProofLoopPhase
from aero_code.web.server import create_app


@pytest.fixture
def dashboard():
    import uvicorn

    bus = ProofLoopEventBus()
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    app = create_app(event_bus=bus)
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.monotonic() + 10
    try:
        while not server.started:
            if not thread.is_alive() or time.monotonic() > deadline:
                pytest.fail("Dashboard test server did not start")
            time.sleep(0.01)
        yield f"http://127.0.0.1:{port}", bus
    finally:
        server.should_exit = True
        thread.join(10)
        assert not thread.is_alive(), "Dashboard test server did not stop"


@pytest.fixture
def page(dashboard):
    playwright = pytest.importorskip("playwright.sync_api")
    with playwright.sync_playwright() as driver:
        try:
            browser = driver.chromium.launch()
        except playwright.Error as exc:
            if "Executable doesn't exist" in str(exc):
                pytest.skip("Install browser test runtime: python -m playwright install chromium")
            raise
        context = browser.new_context(viewport={"width": 1440, "height": 1000})
        tab = context.new_page()
        errors = []
        tab.on("pageerror", lambda error: errors.append(str(error)))
        tab.set_default_timeout(15000)
        tab.goto(dashboard[0])
        tab.locator("#connection-status.connected").wait_for()
        yield tab
        context.close()
        browser.close()
        assert errors == [], f"Uncaught browser errors: {errors}"


@pytest.mark.parametrize("width", [320, 375, 768, 1024, 1440])
def test_dashboard_controls_fit_viewport(page, width):
    page.set_viewport_size({"width": width, "height": 900})
    overflowing = page.locator("button,input,textarea,.matrix-panel,.patch-panel,.header-right").evaluate_all(
        """elements => elements.filter(el => {
            const r = el.getBoundingClientRect();
            return r.left < -1 || r.right > innerWidth + 1;
        }).map(el => el.id || el.className)"""
    )
    assert overflowing == []
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")


def test_presets_clear_required_fields_and_keyboard_submit(page):
    for preset, package in [("requests", "requests"), ("paypal", "paypalrestsdk"), ("pydantic", "pydantic")]:
        page.locator(f"#btn-preset-{preset}").click()
        assert page.locator("#target-package").input_value() == package
        assert page.locator(".btn-preset.active").count() == 1
        assert page.locator(f"#btn-preset-{preset}").get_attribute("aria-pressed") == "true"
    page.locator("#btn-clear-logs").click()
    assert "Log cleared by user" in page.locator("#terminal-logs").inner_text()
    assert page.locator("#terminal-logs .terminal-line").count() == 1
    page.locator("#issue-title").fill("")
    page.locator("#btn-run-loop").click()
    assert page.locator("#issue-title").evaluate("el => !el.checkValidity()")
    assert page.locator("#btn-run-loop").is_enabled()
    page.route("**/api/run", lambda route: route.fulfill(
        status=422, content_type="application/json", body='{"detail":"keyboard validation rejected"}'
    ))
    page.locator("#issue-title").fill("keyboard test")
    page.locator("#issue-title").press("Enter")
    page.locator("#terminal-logs").get_by_text("keyboard validation rejected", exact=False).wait_for()
    assert page.locator("#btn-run-loop").is_enabled()


@pytest.mark.parametrize("status,body,content_type,message", [
    (422, '{"detail":"validation rejected"}', "application/json", "validation rejected"),
    (409, '{"detail":"run already active"}', "application/json", "run already active"),
    (500, "Internal Server Error", "text/plain", "500"),
    (202, "{}", "application/json", "missing a run ID"),
])
def test_http_failure_restores_controls(page, status, body, content_type, message):
    page.route("**/api/run", lambda route: route.fulfill(
        status=status, content_type=content_type, body=body
    ))
    page.locator("#btn-run-loop").click()
    page.locator("#terminal-logs").get_by_text("Failed to trigger ProofLoop", exact=False).wait_for()
    assert message in page.locator("#terminal-logs").inner_text()
    assert page.locator("#btn-run-loop").is_enabled()
    assert page.locator("#issue-title").is_enabled()
    assert page.locator("#verdict-badge").inner_text() == "FAILED"


def test_network_failure_restores_controls(page):
    page.route("**/api/run", lambda route: route.abort("failed"))
    page.locator("#btn-run-loop").click()
    page.locator("#terminal-logs").get_by_text("Failed to trigger ProofLoop", exact=False).wait_for()
    assert page.locator("#btn-run-loop").is_enabled()
    assert page.locator("#verdict-badge").inner_text() == "FAILED"


@pytest.mark.parametrize("preset,source", [
    ("pydantic", "src/models.py"), ("requests", "src/client.py"), ("paypal", "src/webhook.py"),
])
def test_real_preset_flow_results_and_reload(page, preset, source):
    page.locator(f"#btn-preset-{preset}").click()
    page.locator("#btn-run-loop").click()
    assert page.locator("#btn-run-loop").is_disabled()
    assert page.locator("#btn-preset-requests").is_disabled()
    page.locator("#verdict-badge").get_by_text("VERIFIED", exact=True).wait_for(timeout=60000)
    assert page.locator("#btn-run-loop").is_enabled()
    assert page.locator("#stepper-mode").inner_text() == "COMPLETED"
    assert page.locator(".step-node.completed").count() == 9
    assert page.locator(".step-node.active").count() == 0
    assert page.locator(".matrix-status-pill.passed").count() == 4
    assert source in page.locator("#diff-content").inner_text()
    assert page.locator("#citations-list a").count() > 0
    assert page.locator("#primary-model-label").inner_text() == page.request.get(
        page.url + "api/status"
    ).json()["primary_model"]
    page.reload()
    page.locator("#verdict-badge").get_by_text("VERIFIED", exact=True).wait_for()
    assert page.locator(".matrix-status-pill.passed").count() == 4
    assert source in page.locator("#diff-content").inner_text()
    assert page.locator("#btn-run-loop").is_enabled()


def test_sse_safe_citations_failure_and_retry_state(page, dashboard):
    bus = dashboard[1]
    bus.publish("RESEARCH_COMPLETE", {"citations": [{
        "title": "<img src=x onerror=alert(1)>", "url": "javascript:alert(1)", "snippet": "<script>bad</script>"
    }]})
    page.locator("#citations-list").get_by_text("invalid citation link", exact=False).wait_for()
    assert page.locator("#citations-list img,#citations-list script,#citations-list a").count() == 0
    assert "<img" in page.locator("#citations-list").inner_text()
    bus.publish("PHASE_CHANGE", {"phase": "GENERATE_PATCH", "escalated": True})
    bus.publish("GIT_GUARD_VIOLATION", {"violations": ["protected test"]})
    page.locator("#status-gitguard").get_by_text("FAILED", exact=True).wait_for()
    bus.publish("PHASE_CHANGE", {"phase": "GENERATE_PATCH", "escalated": True})
    bus.publish("GIT_GUARD_VERIFIED", {"is_valid": True})
    page.locator("#status-gitguard").get_by_text("PASSED", exact=True).wait_for()
    bus.publish("RUN_FAILED", {"error": "runtime unavailable"}, ProofLoopPhase.FAILED)
    page.locator("#verdict-badge").get_by_text("FAILED", exact=True).wait_for()
    assert page.locator("#btn-run-loop").is_enabled()
    assert page.locator(".step-node.failed").count() == 1


def test_repeated_run_resets_old_evidence_and_reload_during_run(page):
    page.locator("#btn-preset-requests").click()
    page.locator("#btn-run-loop").click()
    page.locator("#verdict-badge").get_by_text("VERIFIED", exact=True).wait_for(timeout=60000)
    assert "src/client.py" in page.locator("#patch-file-label").inner_text()
    page.locator("#btn-preset-paypal").click()
    page.locator("#btn-run-loop").click()
    assert page.locator("#verdict-badge").inner_text() == "RUNNING"
    assert page.locator(".matrix-status-pill.passed").count() == 0
    assert "src/client.py" not in page.locator("#patch-file-label").inner_text()
    page.reload()
    page.locator("#verdict-badge").get_by_text("VERIFIED", exact=True).wait_for(timeout=60000)
    assert "src/webhook.py" in page.locator("#diff-content").inner_text()
    assert page.locator("#btn-run-loop").is_enabled()


def test_polling_recovers_results_while_sse_disconnected(page):
    page.route("**/api/stream", lambda route: route.abort("failed"))
    page.reload()
    page.locator("#connection-label").get_by_text("Reconnecting", exact=False).wait_for()
    page.locator("#btn-preset-requests").click()
    page.locator("#btn-run-loop").click()
    page.locator("#verdict-badge").get_by_text("VERIFIED", exact=True).wait_for(timeout=60000)
    assert page.locator(".matrix-status-pill.passed").count() == 4
    page.unroute("**/api/stream")
    page.locator("#connection-status.connected").wait_for(timeout=15000)
    assert "src/client.py" in page.locator("#diff-content").inner_text()


def test_server_restart_snapshot_accepts_new_event_sequence(page):
    snapshot = {
        "status": "idle", "current_run_id": "old-run", "last_verdict": "INCONCLUSIVE",
        "primary_model": "primary", "escalation_model": "escalation",
        "events": [{
            "sequence": 99, "run_id": "old-run", "event_type": "RUN_COMPLETE",
            "payload": {"verdict": "INCONCLUSIVE"},
        }],
    }
    page.route("**/api/status", lambda route: route.fulfill(json=snapshot))
    page.locator("#verdict-badge").get_by_text("INCONCLUSIVE", exact=True).wait_for()
    snapshot.update(
        current_run_id="new-run", last_verdict=None, status="running",
        events=[{
            "sequence": 1, "run_id": "new-run", "event_type": "PATCH_GENERATED",
            "payload": {"patch": {
                "diffs": [{"file_path": "new.py", "old_content": "", "new_content": "VALUE = 1"}],
                "regression_test_file": "test_new.py", "regression_test_code": "def test_new(): pass",
            }},
        }],
    )
    page.locator("#patch-file-label").get_by_text("new.py", exact=True).wait_for(timeout=7000)
    assert page.locator("#btn-run-loop").is_disabled()
