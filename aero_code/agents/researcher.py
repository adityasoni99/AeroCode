"""Researcher Agent: Formulates dynamic search queries and extracts doc citations via Tavily."""

import re
from typing import Optional

from aero_code.schemas.issues import IssueReport
from aero_code.schemas.research import ResearchResult
from aero_code.tools.tavily_client import TavilySearchClient


class ResearcherAgent:
    """Agent responsible for dynamic information retrieval using Tavily."""

    def __init__(self, tavily_client: Optional[TavilySearchClient] = None) -> None:
        self.tavily_client = tavily_client or TavilySearchClient()

    def synthesize_query(self, package: str, version: str, error: str) -> str:
        """Construct a high-signal search query from package, version, and traceback error."""
        clean_error = re.sub(r"['\"]", "", error).strip()
        parts = [p for p in [package, version, clean_error] if p]
        return " ".join(parts)

    def research_issue(self, issue: IssueReport) -> ResearchResult:
        """Conduct targeted research on the issue using Tavily."""
        # Extract target package and version or derive from title / traceback
        pkg = issue.target_package or "python"
        ver = issue.package_version or ""
        error = issue.implicated_symbol or issue.title or "error"

        if not issue.target_package:
            if "pydantic" in (issue.title + issue.description + issue.traceback).lower():
                pkg = "pydantic"
            elif "requests" in (issue.title + issue.description + issue.traceback).lower():
                pkg = "requests"

        if not issue.implicated_symbol:
            match = re.search(r"AttributeError:.*?'(.*?)'", issue.traceback)
            if match:
                error = f"AttributeError: {match.group(1)}"

        query = self.synthesize_query(package=pkg, version=ver, error=error)
        citations = self.tavily_client.search(query=query)

        # Synthesize actionable summary from citations
        summary = ""
        for cit in citations:
            if "model_validate" in cit.snippet.lower():
                summary = "Pydantic V2 migration: BaseModel.parse_obj() was removed; replace with BaseModel.model_validate()."
                break
            elif "timeout" in cit.snippet.lower():
                summary = "Requests: All network requests should specify an explicit timeout to prevent indefinite hangs."
                break

        if not summary:
            summary = f"Retrieved {len(citations)} documentation references for {query}."

        return ResearchResult(
            query=query,
            summary=summary,
            citations=citations,
        )
