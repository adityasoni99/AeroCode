"""FastAPI backend server for Aero-Code Web Dashboard with SSE streaming."""
import asyncio
from collections import deque
import json
import logging
from pathlib import Path
from threading import RLock
from typing import Any, AsyncGenerator, Dict, Literal, Optional
import uuid

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, field_validator

from aero_code.config import get_settings
from aero_code.orchestrator.loop import ProofLoopOrchestrator
from aero_code.schemas.issues import IssueReport
from aero_code.state import ProofLoopEvent, ProofLoopEventBus, ProofLoopPhase

logger = logging.getLogger(__name__)


class RunRequest(BaseModel):
    issue_id: str = "DEMO-001"
    title: str = "Fix Deprecated Call"
    description: str = "AttributeError on calling deprecated API method"
    traceback: str = ""
    target_package: str = "demo-pkg"
    package_version: str = "1.0.0"
    repo_dir: Optional[str] = None
    case_id: Optional[str] = None
    mode: Literal["demo", "live"] = "demo"

    @field_validator("issue_id", "title", "target_package", "package_version")
    @classmethod
    def nonempty_field(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be blank")
        return value.strip()

def create_app(
    event_bus: Optional[ProofLoopEventBus] = None,
    orchestrator: Optional[ProofLoopOrchestrator] = None,
) -> FastAPI:
    """Create and configure the FastAPI dashboard application."""
    app = FastAPI(title="Aero-Code ProofLoop Dashboard", version="0.1.0")

    bus = event_bus or ProofLoopEventBus()
    settings = get_settings()

    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    # Global runtime state
    state_store: Dict[str, Any] = {
        "status": "idle",
        "current_run_id": None,
        "last_verdict": None,
        "last_error": None,
        "last_report": None,
    }
    lock = RLock()
    events: deque[Dict[str, Any]] = deque(maxlen=256)
    sequence = 0
    completion_published = False

    # Queue for SSE subscribers
    subscribers: list[tuple[asyncio.AbstractEventLoop, asyncio.Queue[str]]] = []

    def bus_listener(event: ProofLoopEvent):
        nonlocal sequence, completion_published
        with lock:
            sequence += 1
            record = event.model_dump(mode="json")
            record.update(sequence=sequence, run_id=state_store["current_run_id"])
            if event.event_type == "RUN_COMPLETE":
                completion_published = True
                report = record["payload"].get("report")
                if report is not None:
                    if state_store["current_run_id"] is not None:
                        report["run_id"] = state_store["current_run_id"]
                    state_store["last_report"] = report
                    state_store["last_verdict"] = record["payload"]["verdict"]
            events.append(record)
            listeners = list(subscribers)
        data = json.dumps(record)
        for loop, queue in listeners:
            try:
                loop.call_soon_threadsafe(queue.put_nowait, data)
            except RuntimeError:
                logger.warning("SSE subscriber event loop closed before delivery")

    bus.subscribe(bus_listener)

    @app.get("/", response_class=HTMLResponse)
    async def get_index():
        index_path = static_dir / "index.html"
        if index_path.exists():
            return HTMLResponse(content=index_path.read_text(encoding="utf-8"))
        return HTMLResponse(
            "<!DOCTYPE html><html><head><title>Aero-Code</title></head>"
            "<body><h1>Aero-Code ProofLoop Dashboard</h1></body></html>"
        )

    @app.get("/api/status")
    async def get_status():
        with lock:
            return {
                **state_store,
                "events": list(events),
                "primary_model": settings.primary_model,
                "escalation_model": settings.escalation_model,
            }

    @app.get("/api/stream")
    async def sse_stream(request: Request):
        queue: asyncio.Queue[str] = asyncio.Queue()
        subscriber = (asyncio.get_running_loop(), queue)
        with lock:
            subscribers.append(subscriber)

        async def event_generator() -> AsyncGenerator[str, None]:
            try:
                # Send initial connection ping
                yield f"event: connected\ndata: {json.dumps({'status': 'connected'})}\n\n"
                yield f"event: snapshot\ndata: {json.dumps(await get_status())}\n\n"
                while True:
                    if await request.is_disconnected():
                        break
                    try:
                        data = await asyncio.wait_for(queue.get(), timeout=25.0)
                        yield f"event: proofloop\ndata: {data}\n\n"
                    except asyncio.TimeoutError:
                        # Keep-alive heartbeat
                        yield ": ping\n\n"
            finally:
                with lock:
                    if subscriber in subscribers:
                        subscribers.remove(subscriber)

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    def _execute_run(issue: IssueReport, repo_dir: str, mode: str, run_id: str):
        try:
            orch = orchestrator or ProofLoopOrchestrator(mode=mode, event_bus=bus)
            report = orch.run(issue=issue, repo_dir=repo_dir)
            report = report.model_copy(update={"run_id": run_id})
            with lock:
                state_store["last_verdict"] = report.verdict.value
                state_store["last_report"] = report.model_dump(mode="json")
                should_publish = not completion_published
            if should_publish:
                bus.publish(
                    "RUN_COMPLETE",
                    {"verdict": report.verdict.value, "report": report.model_dump(mode="json")},
                    ProofLoopPhase.COMPLETED,
                )
        except Exception as exc:
            logger.exception("ProofLoop run %s failed", run_id)
            with lock:
                state_store["last_error"] = str(exc)
                state_store["last_verdict"] = "FAILED"
            bus.publish("RUN_FAILED", {"error": str(exc)}, ProofLoopPhase.FAILED)
        finally:
            with lock:
                state_store["status"] = "idle"

    @app.post("/api/run")
    async def trigger_run(payload: RunRequest, background_tasks: BackgroundTasks):
        nonlocal completion_published
        run_id = f"aero-{uuid.uuid4().hex[:8]}"
        issue = IssueReport(
            issue_id=payload.issue_id,
            title=payload.title,
            description=payload.description,
            traceback=payload.traceback,
            target_package=payload.target_package,
            package_version=payload.package_version,
        )

        if payload.repo_dir is not None:
            repo = Path(payload.repo_dir).resolve()
            if not repo.is_dir():
                raise HTTPException(status_code=400, detail="Repository directory does not exist")
        else:
            from benchmarks.evaluate import BenchmarkSuite

            case_id = payload.case_id or "pydantic_v2_migration"
            case = next((case for case in BenchmarkSuite().load_cases() if case.case_id == case_id), None)
            if case is None:
                raise HTTPException(status_code=404, detail="Unknown benchmark case")
            repo = case.repo_dir

        with lock:
            if state_store["status"] == "running":
                raise HTTPException(status_code=409, detail="A ProofLoop run is already in progress")
            state_store.update(
                status="running", current_run_id=run_id, last_verdict=None,
                last_error=None, last_report=None,
            )
            events.clear()
            completion_published = False
        bus.publish("RUN_STARTED", {"run_id": run_id, "mode": payload.mode})

        background_tasks.add_task(
            _execute_run, issue, str(repo), payload.mode, run_id
        )

        return JSONResponse(
            status_code=202,
            content={
                "message": "ProofLoop run initiated",
                "run_id": run_id,
                "status": "running",
            },
        )

    return app
