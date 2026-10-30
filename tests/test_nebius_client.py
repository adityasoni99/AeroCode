# tests/test_nebius_client.py
from aero_code.llm.client import NebiusNemotronClient
from aero_code.config import Settings

def test_nebius_client_demo_mode():
    client = NebiusNemotronClient(mode="demo")
    resp = client.investigate(
        issue_title="Pydantic parse_obj error",
        traceback="AttributeError: 'UserModel' has no attribute 'parse_obj'"
    )
    assert resp.implicated_symbol == "parse_obj"
    assert "pydantic" in resp.root_cause.lower()

def test_nebius_client_escalation_model():
    client = NebiusNemotronClient(mode="demo")
    patch = client.generate_patch(
        issue_title="Pydantic parse_obj error",
        source_code="class UserModel:\n    pass",
        research_context="Use model_validate in Pydantic v2",
        escalate=True
    )
    assert patch.regression_test_code != ""
