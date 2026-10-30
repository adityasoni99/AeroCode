# tests/test_report_generator.py
from aero_code.verifier.report_generator import EvidenceReportGenerator
from aero_code.schemas.report import EvidenceReport, VerificationVerdict
from aero_code.schemas.research import TavilyCitation
from aero_code.schemas.patch import PatchProposal, FileDiff

def test_evidence_report_markdown_and_json():
    gen = EvidenceReportGenerator()
    report = gen.generate(
        run_id="aero-proof-20261028-001",
        repository="owner/repo",
        baseline_commit="a1b2c3d4",
        patch_commit="e5f6g7h8",
        model_used="nvidia/Nemotron-3.5-Lightning",
        citations=[TavilyCitation(title="Pydantic Docs", url="https://docs.pydantic.dev/migration", snippet="Use model_validate")],
        patch=PatchProposal(diffs=[FileDiff(file_path="app.py", old_content="old", new_content="new")]),
        baseline_test_passed=False,
        patched_test_passed=True,
        baseline_suite_passed=True,
        git_guard_passed=True,
        verdict=VerificationVerdict.VERIFIED
    )
    assert report.verdict == VerificationVerdict.VERIFIED
    md = gen.to_markdown(report)
    assert "Double-Verification Matrix" in md
    assert "https://docs.pydantic.dev/migration" in md
    assert "VERIFIED" in md
