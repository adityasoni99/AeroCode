# tests/test_state_machine.py
import tempfile
from pathlib import Path
from aero_code.orchestrator.loop import ProofLoopOrchestrator
from aero_code.schemas.issues import IssueReport
from aero_code.schemas.report import VerificationVerdict
from aero_code.state import ProofLoopEventBus

def test_proofloop_full_run():
    bus = ProofLoopEventBus()
    states_visited = []
    bus.subscribe(lambda e: states_visited.append(e.event_type))

    orchestrator = ProofLoopOrchestrator(mode="demo", event_bus=bus, max_retries=2)
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo = Path(tmp_dir)
        (repo / "src").mkdir()
        (repo / "tests").mkdir()
        (repo / "src" / "service.py").write_text("def run():\n    return 'deprecated_call'\n")
        (repo / "tests" / "test_baseline.py").write_text("def test_ok(): assert True\n")

        issue = IssueReport(
            issue_id="ISSUE-DEMO",
            title="Service failure",
            description="Deprecated call should be modern_call",
            traceback="AttributeError: deprecated_call",
            target_package="demo-pkg",
            package_version="1.0.0"
        )

        report = orchestrator.run(issue=issue, repo_dir=str(repo))
        assert report.verdict in (VerificationVerdict.VERIFIED, VerificationVerdict.INCONCLUSIVE)
        assert "PHASE_CHANGE" in states_visited
