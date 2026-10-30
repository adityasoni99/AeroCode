"""Tavily search client with live SDK integration and curated demo fallback fixtures."""

import os
from typing import List, Optional
from tavily import TavilyClient

from aero_code.config import Settings
from aero_code.schemas.research import TavilyCitation


class TavilySearchClient:
    """Retrieves authoritative documentation and migration guides via Tavily API."""

    DEMO_CITATIONS = {
        "pydantic": [
            TavilyCitation(
                title="Pydantic Migration Guide: V1 to V2",
                url="https://docs.pydantic.dev/latest/migration/",
                snippet="BaseModel.parse_obj() was removed in Pydantic V2. Use BaseModel.model_validate(obj) instead.",
            ),
            TavilyCitation(
                title="Pydantic V2 Changes & Deprecations",
                url="https://docs.pydantic.dev/2.0/migration/#changes-to-pydanticbasemodel",
                snippet="parse_obj, parse_raw, and from_orm have been superseded by model_validate and model_validate_json.",
            ),
        ],
        "requests": [
            TavilyCitation(
                title="Requests: Timeouts and Reliability",
                url="https://requests.readthedocs.io/en/latest/user/advanced/#timeouts",
                snippet="Nearly all production code should use this parameter in all requests. Failure to do so can cause your program to hang indefinitely.",
            ),
        ],
    }

    def __init__(self, api_key: Optional[str] = None, mode: Optional[str] = None) -> None:
        settings = Settings()
        self.api_key = api_key or settings.tavily_api_key or os.environ.get("TAVILY_API_KEY", "")
        self.mode = mode or settings.mode
        self._client: Optional[TavilyClient] = None

    def search(self, query: str, max_results: int = 5) -> List[TavilyCitation]:
        """Query Tavily search engine or return curated demo documentation."""
        if self.mode == "demo" or not self.api_key:
            q_lower = query.lower()
            for key, citations in self.DEMO_CITATIONS.items():
                if key in q_lower:
                    return citations[:max_results]
            return [
                TavilyCitation(
                    title="Python Documentation & Community Solution",
                    url="https://docs.python.org/3/library/",
                    snippet=f"Relevant documentation and solutions for query: {query}",
                )
            ]

        if self._client is None:
            self._client = TavilyClient(api_key=self.api_key)

        try:
            response = self._client.search(
                query=query,
                search_depth="advanced",
                max_results=max_results,
            )
            citations: List[TavilyCitation] = []
            for item in response.get("results", []):
                citations.append(
                    TavilyCitation(
                        title=item.get("title", "Reference"),
                        url=item.get("url", ""),
                        snippet=item.get("content", ""),
                    )
                )
            return citations
        except Exception:
            # Fallback gracefully if live API call fails or quota exhausted
            return [
                TavilyCitation(
                    title="Fallback Documentation Reference",
                    url="https://docs.python.org/3/",
                    snippet=f"Live search encountered fallback for {query}",
                )
            ]
