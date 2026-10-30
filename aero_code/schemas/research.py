"""Tavily search queries, excerpts, and citation schemas."""

from typing import List
from pydantic import BaseModel, Field


class TavilyCitation(BaseModel):
    """A citation referencing documentation retrieved via Tavily Search."""

    title: str
    url: str
    snippet: str


class ResearchResult(BaseModel):
    """Contextual research output with search query, synthesized summary, and citations."""

    query: str
    summary: str = ""
    citations: List[TavilyCitation] = Field(default_factory=list)
