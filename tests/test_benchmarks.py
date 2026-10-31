# tests/test_benchmarks.py
from unittest.mock import MagicMock
from benchmarks.evaluate import BenchmarkSuite, BenchmarkCase
from aero_code.schemas.report import EvidenceReport, VerificationVerdict


def test_benchmark_suite_loading():
    suite = BenchmarkSuite()
    cases = suite.load_cases()
    assert len(cases) >= 3
    assert any(c.case_id == "pydantic_v2_migration" for c in cases)
    assert any(c.case_id == "requests_timeout_kwarg" for c in cases)
    assert any(c.case_id == "paypal_webhook_signature" for c in cases)


def test_benchmark_suite_run_all():
    suite = BenchmarkSuite()
    mock_orchestrator = MagicMock()
    mock_report = MagicMock(spec=EvidenceReport)
    mock_report.verdict = VerificationVerdict.VERIFIED
    mock_report.baseline_test_passed = False  # False means regression test failed on baseline (repro succeeded)
    mock_report.patched_test_passed = True
    mock_report.baseline_suite_passed = True
    mock_report.git_guard_passed = True
    mock_orchestrator.run.return_value = mock_report

    metrics = suite.run_all(orchestrator=mock_orchestrator)
    assert metrics.total_cases >= 2
    assert metrics.reproduced_count == metrics.total_cases
    assert metrics.repaired_count == metrics.total_cases
    assert metrics.verification_rate == 1.0
