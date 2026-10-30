# tests/test_agents.py
from aero_code.agents.investigator import InvestigatorAgent
from aero_code.agents.patch_engineer import PatchEngineerAgent
from aero_code.llm.client import NebiusNemotronClient
from aero_code.schemas.issues import IssueReport
from aero_code.schemas.research import ResearchResult, TavilyCitation

def test_investigator_extracts_root_cause():
    llm = NebiusNemotronClient(mode="demo")
    investigator = InvestigatorAgent(llm_client=llm)
    issue = IssueReport(
        issue_id="ISSUE-1",
        title="Pydantic parse_obj error",
        description="UserModel.parse_obj does not exist",
        traceback="AttributeError: 'UserModel' has no attribute 'parse_obj'",
        target_package="pydantic",
        package_version="2.6.1"
    )
    inv = investigator.analyze(issue)
    assert inv.implicated_symbol == "parse_obj"

def test_patch_engineer_synthesizes_patch_and_regression_test():
    llm = NebiusNemotronClient(mode="demo")
    engineer = PatchEngineerAgent(llm_client=llm)
    patch = engineer.create_patch(
        issue_title="Pydantic error",
        source_code="data = UserModel.parse_obj(payload)",
        research_context="Replaced with model_validate in Pydantic v2"
    )
    assert len(patch.diffs) > 0
    assert "def test_" in patch.regression_test_code
