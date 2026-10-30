"""Benchmark evaluation suite for Aero-Code."""
from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Dict, List, Optional
import shutil
import tempfile

from aero_code.orchestrator.loop import ProofLoopOrchestrator
from aero_code.schemas.issues import IssueReport
from aero_code.schemas.report import EvidenceReport, VerificationVerdict


@dataclass
class BenchmarkCase:
    case_id: str
    issue: IssueReport
    repo_dir: Path
    metadata: Dict = field(default_factory=dict)


@dataclass
class BenchmarkMetrics:
    total_cases: int
    reproduced_count: int
    repaired_count: int
    verified_count: int
    reproduction_rate: float
    repair_rate: float
    verification_rate: float
    case_results: Dict[str, Dict] = field(default_factory=dict)


class BenchmarkSuite:
    def __init__(self, cases_dir: Optional[Path] = None):
        if cases_dir is None:
            self.cases_dir = Path(__file__).parent / "cases"
        else:
            self.cases_dir = Path(cases_dir)

    def load_cases(self) -> List[BenchmarkCase]:
        """Discover and load all benchmark cases under cases_dir."""
        cases = []
        if not self.cases_dir.exists():
            return cases

        for case_folder in sorted(self.cases_dir.iterdir()):
            if not case_folder.is_dir():
                continue
            issue_file = case_folder / "issue.json"
            repo_folder = case_folder / "repo"
            if issue_file.exists() and repo_folder.exists():
                with open(issue_file, "r", encoding="utf-8") as f:
                    issue_data = json.load(f)
                issue = IssueReport(
                    issue_id=issue_data.get("issue_id", case_folder.name),
                    title=issue_data.get("title", ""),
                    description=issue_data.get("description", ""),
                    traceback=issue_data.get("traceback", ""),
                    target_package=issue_data.get("target_package", ""),
                    package_version=issue_data.get("package_version", ""),
                )
                cases.append(
                    BenchmarkCase(
                        case_id=case_folder.name,
                        issue=issue,
                        repo_dir=repo_folder,
                        metadata=issue_data,
                    )
                )
        return cases

    def run_case(
        self, case: BenchmarkCase, orchestrator: Optional[ProofLoopOrchestrator] = None
    ) -> Dict:
        """Run a single benchmark case against a fresh temporary copy of repo."""
        if orchestrator is None:
            orchestrator = ProofLoopOrchestrator(mode="demo")

        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_repo = Path(tmp_dir) / "repo"
            shutil.copytree(case.repo_dir, temp_repo)

            report = orchestrator.run(issue=case.issue, repo_dir=str(temp_repo))
            is_reproduced = not report.baseline_test_passed
            is_repaired = report.patched_test_passed
            is_verified = report.verdict == VerificationVerdict.VERIFIED

            return {
                "case_id": case.case_id,
                "reproduced": is_reproduced,
                "repaired": is_repaired,
                "verified": is_verified,
                "verdict": report.verdict.value,
                "report": report,
            }

    def run_all(
        self, orchestrator: Optional[ProofLoopOrchestrator] = None
    ) -> BenchmarkMetrics:
        """Run all discovered benchmark cases and compute metrics."""
        cases = self.load_cases()
        results = {}
        reproduced = 0
        repaired = 0
        verified = 0

        for case in cases:
            res = self.run_case(case, orchestrator=orchestrator)
            results[case.case_id] = res
            if res["reproduced"]:
                reproduced += 1
            if res["repaired"]:
                repaired += 1
            if res["verified"]:
                verified += 1

        total = len(cases)
        return BenchmarkMetrics(
            total_cases=total,
            reproduced_count=reproduced,
            repaired_count=repaired,
            verified_count=verified,
            reproduction_rate=reproduced / total if total > 0 else 0.0,
            repair_rate=repaired / total if total > 0 else 0.0,
            verification_rate=verified / total if total > 0 else 0.0,
            case_results=results,
        )
