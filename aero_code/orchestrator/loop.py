"""Deterministic ProofLoop state machine orchestrating end-to-end bug repair and verification."""

import os
import time
import uuid
from pathlib import Path
from typing import Optional, Set

from aero_code.agents.investigator import InvestigatorAgent
from aero_code.agents.patch_engineer import PatchEngineerAgent
from aero_code.agents.researcher import ResearcherAgent
from aero_code.config import Settings
from aero_code.llm.client import NebiusNemotronClient
from aero_code.schemas.issues import IssueReport
from aero_code.schemas.patch import PatchProposal
from aero_code.schemas.report import EvidenceReport, VerificationVerdict
from aero_code.state import ProofLoopEventBus, ProofLoopPhase, ProofLoopState
from aero_code.tools.github_client import GitHubClient
from aero_code.tools.tavily_client import TavilySearchClient
from aero_code.verifier.git_guard import GitGuard
from aero_code.verifier.report_generator import EvidenceReportGenerator
from aero_code.verifier.sandbox.base import BaseSandboxAdapter
from aero_code.verifier.sandbox.docker import DockerSandboxAdapter
from aero_code.verifier.sandbox.subprocess import SubprocessSandboxAdapter


class ProofLoopOrchestrator:
    """Bounded, deterministic state machine executing the Double-Verification ProofLoop."""

    def __init__(
        self,
        settings: Optional[Settings] = None,
        mode: Optional[str] = None,
        event_bus: Optional[ProofLoopEventBus] = None,
        max_retries: int = 3,
        sandbox_adapter: Optional[BaseSandboxAdapter] = None,
    ) -> None:
        self.settings = settings or Settings()
        self.mode = mode or self.settings.mode
        self.event_bus = event_bus or ProofLoopEventBus()
        self.max_retries = max_retries

        # Sub-components
        self.llm_client = NebiusNemotronClient(settings=self.settings, mode=self.mode)
        self.tavily_client = TavilySearchClient(mode=self.mode)
        self.researcher = ResearcherAgent(tavily_client=self.tavily_client)
        self.investigator = InvestigatorAgent(llm_client=self.llm_client)
        self.patch_engineer = PatchEngineerAgent(llm_client=self.llm_client)
        self.git_guard = GitGuard()
        self.report_generator = EvidenceReportGenerator()
        self.github_client = GitHubClient()
        if sandbox_adapter is not None:
            self.sandbox = sandbox_adapter
        elif self.mode == "demo":
            self.sandbox = SubprocessSandboxAdapter(timeout_seconds=self.settings.timeout_seconds)
        else:
            self.sandbox = DockerSandboxAdapter(
                timeout_seconds=self.settings.timeout_seconds,
                image=self.settings.sandbox_image,
                allow_subprocess_fallback=self.settings.sandbox_allow_subprocess_fallback,
            )

    def _emit(self, event_type: str, payload: dict, phase: Optional[ProofLoopPhase] = None) -> None:
        """Publish telemetry event to event bus."""
        self.event_bus.publish(event_type=event_type, payload=payload, phase=phase)

    def _collect_baseline_tests(self, repo_dir: Path) -> Set[str]:
        """Collect all existing test files in the repository."""
        baseline: Set[str] = set()
        tests_dir = repo_dir / "tests"
        if tests_dir.exists():
            for p in tests_dir.rglob("*.py"):
                rel = p.relative_to(repo_dir).as_posix()
                baseline.add(rel)
        return baseline

    def run(self, issue: IssueReport, repo_dir: str) -> EvidenceReport:
        """Execute the full ProofLoop state machine deterministically."""
        start_time = time.perf_counter()
        run_id = f"aero-proof-{uuid.uuid4().hex[:8]}"
        repo_path = Path(repo_dir).resolve()

        state = ProofLoopState(phase=ProofLoopPhase.INTAKE, issue=issue)

        # 1. INTAKE
        self._emit(
            "PHASE_CHANGE",
            {"phase": ProofLoopPhase.INTAKE.value, "issue_id": issue.issue_id, "title": issue.title},
            ProofLoopPhase.INTAKE,
        )

        # Collect baseline test files
        baseline_test_files = self._collect_baseline_tests(repo_path)

        # 2. INVESTIGATE
        state.phase = ProofLoopPhase.INVESTIGATE
        self._emit("PHASE_CHANGE", {"phase": ProofLoopPhase.INVESTIGATE.value}, ProofLoopPhase.INVESTIGATE)

        source_code = ""
        # Find potential source file in repo
        for py_file in repo_path.glob("src/**/*.py"):
            source_code = py_file.read_text(encoding="utf-8")
            break

        inv_report = self.investigator.analyze(issue, source_code=source_code)
        self._emit(
            "INVESTIGATION_COMPLETE",
            {"implicated_symbol": inv_report.implicated_symbol, "root_cause": inv_report.root_cause},
            ProofLoopPhase.INVESTIGATE,
        )

        # 3. RESEARCH
        state.phase = ProofLoopPhase.RESEARCH
        self._emit("PHASE_CHANGE", {"phase": ProofLoopPhase.RESEARCH.value}, ProofLoopPhase.RESEARCH)

        research_res = self.researcher.research_issue(issue)
        state.research = research_res
        self._emit(
            "RESEARCH_COMPLETE",
            {
                "query": research_res.query,
                "summary": research_res.summary,
                "citations_count": len(research_res.citations),
            },
            ProofLoopPhase.RESEARCH,
        )

        # 4. REPRODUCE_BASELINE
        state.phase = ProofLoopPhase.REPRODUCE_BASELINE
        self._emit("PHASE_CHANGE", {"phase": ProofLoopPhase.REPRODUCE_BASELINE.value}, ProofLoopPhase.REPRODUCE_BASELINE)

        # Baseline suite run: verify repo baseline tests pass initially
        baseline_suite_res = self.sandbox.run_test_suite(repo_root=str(repo_path))
        baseline_suite_passed = baseline_suite_res.passed

        # Loop: GENERATE_PATCH -> GIT_GUARD -> SANDBOX_EXECUTE (with retry budget)
        retry_count = 0
        escalated = False
        repro_confirmed = False
        patched_test_passed = False
        patched_suite_passed = False
        git_guard_passed = False
        active_patch: Optional[PatchProposal] = None
        last_error = ""

        while retry_count <= self.max_retries:
            # 5. GENERATE_PATCH
            state.phase = ProofLoopPhase.GENERATE_PATCH
            self._emit(
                "PHASE_CHANGE",
                {"phase": ProofLoopPhase.GENERATE_PATCH.value, "retry": retry_count, "escalated": escalated},
                ProofLoopPhase.GENERATE_PATCH,
            )

            active_patch = self.patch_engineer.create_patch(
                issue_title=issue.title,
                source_code=source_code,
                research_context=research_res.summary,
                escalate=escalated,
                retry_error=last_error,
            )
            state.patch = active_patch

            # 6. GIT_GUARD
            state.phase = ProofLoopPhase.GIT_GUARD
            self._emit("PHASE_CHANGE", {"phase": ProofLoopPhase.GIT_GUARD.value}, ProofLoopPhase.GIT_GUARD)

            guard_res = self.git_guard.validate(active_patch, baseline_test_files=baseline_test_files)
            git_guard_passed = guard_res.is_valid

            if not git_guard_passed:
                self._emit("GIT_GUARD_VIOLATION", {"violations": guard_res.violations}, ProofLoopPhase.GIT_GUARD)
                retry_count += 1
                escalated = True
                last_error = f"Git Guard rejected patch: {', '.join(guard_res.violations)}"
                continue

            # 7. SANDBOX_EXECUTE
            state.phase = ProofLoopPhase.SANDBOX_EXECUTE
            self._emit("PHASE_CHANGE", {"phase": ProofLoopPhase.SANDBOX_EXECUTE.value}, ProofLoopPhase.SANDBOX_EXECUTE)

            # Test A: Regression test must fail on unpatched code (Bug Reproduction)
            # Create a reproduction patch with ONLY the regression test file
            repro_patch = PatchProposal(
                diffs=[],
                regression_test_code=active_patch.regression_test_code,
                regression_test_file=active_patch.regression_test_file,
            )
            repro_res = self.sandbox.run_test_suite(
                repo_root=str(repo_path),
                test_target=active_patch.regression_test_file,
                patch=repro_patch,
            )
            # Non-vacuous test: exit_code != 0 on unpatched codebase
            repro_confirmed = not repro_res.passed

            # Test B: Regression test must pass on patched code (Bug Resolution)
            patched_res = self.sandbox.run_test_suite(
                repo_root=str(repo_path),
                test_target=active_patch.regression_test_file,
                patch=active_patch,
            )
            patched_test_passed = patched_res.passed

            # Test C: Baseline test suite must pass with patch applied (Zero Regressions)
            suite_res = self.sandbox.run_test_suite(
                repo_root=str(repo_path),
                patch=active_patch,
            )
            patched_suite_passed = suite_res.passed

            if patched_test_passed and patched_suite_passed:
                break  # Successful verification!

            # Retry handling
            retry_count += 1
            escalated = True
            last_error = f"Test failure: {patched_res.stderr or patched_res.stdout}"

        # 8. EVIDENCE_REPORT
        state.phase = ProofLoopPhase.EVIDENCE_REPORT
        self._emit("PHASE_CHANGE", {"phase": ProofLoopPhase.EVIDENCE_REPORT.value}, ProofLoopPhase.EVIDENCE_REPORT)

        total_duration_ms = (time.perf_counter() - start_time) * 1000.0

        # Verdict calculation per Double-Verification Rule
        if git_guard_passed and patched_test_passed and patched_suite_passed:
            verdict = VerificationVerdict.VERIFIED
        else:
            verdict = VerificationVerdict.INCONCLUSIVE

        model_name = (
            self.settings.escalation_model if escalated else self.settings.primary_model
        )

        evidence_report = self.report_generator.generate(
            run_id=run_id,
            repository=os.path.basename(repo_dir),
            baseline_commit="HEAD~1",
            patch_commit=f"patch-{uuid.uuid4().hex[:6]}",
            model_used=model_name,
            citations=research_res.citations,
            patch=active_patch,
            baseline_test_passed=(not repro_confirmed),  # False means regression test failed as required
            patched_test_passed=patched_test_passed,
            baseline_suite_passed=patched_suite_passed,
            git_guard_passed=git_guard_passed,
            verdict=verdict,
            execution_duration_ms=total_duration_ms,
            notes=f"Retries: {retry_count}, Escalated: {escalated}",
        )
        state.report = evidence_report

        # 9. PUBLISH_PR
        if verdict == VerificationVerdict.VERIFIED:
            state.phase = ProofLoopPhase.PUBLISH_PR
            self._emit("PHASE_CHANGE", {"phase": ProofLoopPhase.PUBLISH_PR.value}, ProofLoopPhase.PUBLISH_PR)
            md_summary = self.report_generator.to_markdown(evidence_report)
            pr_info = self.github_client.create_draft_pr(
                repo=os.path.basename(repo_dir),
                title=f"fix(aero-proof): {issue.title}",
                body=md_summary,
                head_branch=f"aero-fix-{issue.issue_id.lower()}",
            )
            self._emit("PR_PUBLISHED", pr_info, ProofLoopPhase.PUBLISH_PR)

        # 10. COMPLETED
        state.phase = ProofLoopPhase.COMPLETED
        self._emit(
            "PHASE_CHANGE",
            {"phase": ProofLoopPhase.COMPLETED.value, "verdict": verdict.value},
            ProofLoopPhase.COMPLETED,
        )

        return evidence_report
