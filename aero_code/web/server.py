"""FastAPI backend server for Aero-Code Web Dashboard with SSE streaming."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, Optional
import uuid

from fastapi import BackgroundTasks, FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from aero_code.config import get_settings
from aero_code.orchestrator.loop import ProofLoopOrchestrator
from aero_code.schemas.issues import IssueReport
from aero_code.state import ProofLoopEvent, ProofLoopEventBus, ProofLoopPhase


class RunRequest(BaseModel):
    issue_id: str = "DEMO-001"
    title: str = "Fix Deprecated Call"
    description: str = "AttributeError on calling deprecated API method"
    traceback: str = ""
    target_package: str = "demo-pkg"
    package_version: str = "1.0.0"
    repo_dir: Optional[str] = None
    mode: str = "demo"


_executor = ThreadPoolExecutor(max_workers=2)


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
        "history": [],
    }

    # Queue for SSE subscribers
    subscribers: list[asyncio.Queue] = []

    def bus_listener(event: ProofLoopEvent):
        data = event.model_dump_json()
        for q in list(subscribers):
            try:
                q.put_nowait(data)
            except Exception:
                pass

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
        return {
            "status": state_store["status"],
            "current_run_id": state_store["current_run_id"],
            "last_verdict": state_store["last_verdict"],
            "primary_model": settings.primary_model,
            "escalation_model": settings.escalation_model,
        }

    @app.get("/api/stream")
    async def sse_stream(request: Request):
        queue: asyncio.Queue = asyncio.Queue()
        subscribers.append(queue)

        async def event_generator() -> AsyncGenerator[str, None]:
            try:
                # Send initial connection ping
                yield f"event: connected\ndata: {json.dumps({'status': 'connected'})}\n\n"
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
                if queue in subscribers:
                    subscribers.remove(queue)

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
        state_store["status"] = "running"
        state_store["current_run_id"] = run_id
        try:
            orch = orchestrator or ProofLoopOrchestrator(mode=mode, event_bus=bus)
            report = orch.run(issue=issue, repo_dir=repo_dir)
            state_store["last_verdict"] = report.verdict.value
            state_store["history"].append(report.model_dump())
        finally:
            state_store["status"] = "idle"

    @app.post("/api/run")
    async def trigger_run(payload: RunRequest, background_tasks: BackgroundTasks):
        run_id = f"aero-{uuid.uuid4().hex[:8]}"
        issue = IssueReport(
            issue_id=payload.issue_id,
            title=payload.title,
            description=payload.description,
            traceback=payload.traceback,
            target_package=payload.target_package,
            package_version=payload.package_version,
        )

        repo_dir = payload.repo_dir or str(Path.cwd())

        # If repo_dir has no tests, point to a sample benchmark repo
        default_benchmark = (
            Path(__file__).parent.parent.parent
            / "benchmarks"
            / "cases"
            / "pydantic_v2_migration"
            / "repo"
        )
        if not (Path(repo_dir) / "tests").exists() and default_benchmark.exists():
            repo_dir = str(default_benchmark)

        background_tasks.add_task(
            _execute_run, issue, repo_dir, payload.mode, run_id
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
