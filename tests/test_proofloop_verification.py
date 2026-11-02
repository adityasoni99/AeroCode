from pathlib import Path

import pytest

from aero_code.config import Settings
from aero_code.orchestrator.loop import ProofLoopOrchestrator
from aero_code.schemas.issues import IssueReport
from aero_code.schemas.report import VerificationVerdict
from aero_code.state import ProofLoopEventBus
from aero_code.verifier.sandbox.base import BaseSandboxAdapter, SandboxExecutionResult
from benchmarks.evaluate import BenchmarkSuite


class ScriptedSandbox(BaseSandboxAdapter):
    def __init__(self, repro_exit):
        super().__init__()
        self.repro_exit = repro_exit

    def run_test_suite(self, repo_root, test_target=None, patch=None):
        code = self.repro_exit if patch is not None and not patch.diffs else 0
        return SandboxExecutionResult(
            exit_code=code, passed=code == 0, stdout="pytest", stderr="", duration_ms=1
        )


@pytest.mark.parametrize("repro_exit", [0, -1, 2, 3, 4, 5, 137])
def test_only_assertion_failure_confirms_bug_reproduction(tmp_path, repro_exit):
    bus = ProofLoopEventBus()
    events = []
    bus.subscribe(events.append)
    orchestrator = ProofLoopOrchestrator(
        settings=Settings(_env_file=None), mode="demo", event_bus=bus,
        max_retries=0, sandbox_adapter=ScriptedSandbox(repro_exit),
    )
    report = orchestrator.run(
        IssueReport(issue_id="NO-REPRO", title="No bug", description="No failure"), str(tmp_path)
    )
    assert report.verdict == VerificationVerdict.INCONCLUSIVE
    assert not any(event.event_type == "PR_PUBLISHED" for event in events)
    verification = next(e for e in events if e.event_type == "DOUBLE_VERIFICATION_COMPLETE")
    assert verification.payload["baseline_passed"] is True
    assert events[-1].event_type == "RUN_COMPLETE"


def test_completed_run_emits_all_dashboard_evidence(tmp_path):
    events = []
    bus = ProofLoopEventBus()
    bus.subscribe(events.append)
    orchestrator = ProofLoopOrchestrator(
        mode="demo", event_bus=bus, max_retries=0, sandbox_adapter=ScriptedSandbox(1)
    )
    report = orchestrator.run(
        IssueReport(issue_id="REPRO", title="Demo bug", description="Failing regression"),
        str(tmp_path),
    )
    assert report.verdict == VerificationVerdict.VERIFIED
    by_type = {e.event_type: e for e in events}
    assert by_type["RESEARCH_COMPLETE"].payload["citations"]
    assert by_type["PATCH_GENERATED"].payload["patch"]["regression_test_code"]
    assert by_type["GIT_GUARD_VERIFIED"].payload["is_valid"] is True
    assert by_type["DOUBLE_VERIFICATION_COMPLETE"].payload["baseline_passed"] is False
    assert by_type["RUN_COMPLETE"].payload["verdict"] == "VERIFIED"


@pytest.mark.parametrize("case_id", [
    "pydantic_v2_migration", "requests_timeout_kwarg", "paypal_webhook_signature",
])
def test_seeded_presets_double_verify_with_real_subprocess(case_id):
    suite = BenchmarkSuite()
    case = next(case for case in suite.load_cases() if case.case_id == case_id)
    result = suite.run_case(case, ProofLoopOrchestrator(mode="demo", max_retries=0))
    assert result["verified"], result["report"].notes
    assert result["reproduced"]
    assert result["repaired"]
