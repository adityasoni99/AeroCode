# tests/test_schemas_and_state.py
import pytest
from aero_code.config import Settings
from aero_code.schemas.issues import IssueReport
from aero_code.schemas.patch import PatchProposal, FileDiff
from aero_code.schemas.research import ResearchResult, TavilyCitation
from aero_code.schemas.report import EvidenceReport, VerificationVerdict
from aero_code.state import ProofLoopState, ProofLoopPhase, ProofLoopEventBus

def test_settings_defaults():
    s = Settings()
    assert s.nebius_base_url == "https://api.tokenfactory.nebius.com/v1/"
    assert s.primary_model == "nvidia/Nemotron-3.5-Lightning"

def test_schemas_instantiation():
    issue = IssueReport(
        issue_id="ISSUE-101",
        title="Pydantic parse_obj deprecated",
        description="AttributeError when calling UserModel.parse_obj()",
        traceback="AttributeError: type object 'UserModel' has no attribute 'parse_obj'",
        target_package="pydantic",
        package_version="2.6.1"
    )
    assert issue.issue_id == "ISSUE-101"

    diff = FileDiff(file_path="app/models.py", old_content="UserModel.parse_obj()", new_content="UserModel.model_validate()")
    patch = PatchProposal(diffs=[diff], regression_test_code="def test_regression(): pass")
    assert len(patch.diffs) == 1

def test_event_bus():
    bus = ProofLoopEventBus()
    events = []
    bus.subscribe(lambda e: events.append(e))
    bus.publish("TEST_EVENT", {"detail": "hello"})
    assert len(events) == 1
    assert events[0].event_type == "TEST_EVENT"
