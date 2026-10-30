# tests/test_tavily_search.py
from aero_code.tools.tavily_client import TavilySearchClient
from aero_code.agents.researcher import ResearcherAgent
from aero_code.schemas.issues import IssueReport

def test_dynamic_query_synthesis():
    agent = ResearcherAgent(tavily_client=TavilySearchClient(mode="demo"))
    query = agent.synthesize_query(
        package="pydantic",
        version="2.6.1",
        error="AttributeError: parse_obj"
    )
    assert "pydantic" in query
    assert "2.6.1" in query
    assert "parse_obj" in query

def test_research_execution_returns_citations():
    agent = ResearcherAgent(tavily_client=TavilySearchClient(mode="demo"))
    issue = IssueReport(
        issue_id="ISSUE-1",
        title="AttributeError in parse_obj",
        description="Calling parse_obj fails",
        traceback="AttributeError: type object 'UserModel' has no attribute 'parse_obj'",
        target_package="pydantic",
        package_version="2.6.1"
    )
    result = agent.research_issue(issue)
    assert len(result.citations) > 0
    assert result.citations[0].url.startswith("http")
    assert "model_validate" in result.summary.lower()
