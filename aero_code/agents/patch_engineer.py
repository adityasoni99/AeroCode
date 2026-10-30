"""Patch Engineer Agent: Produces minimal AST/source fixes and isolated regression tests."""

from typing import Optional

from aero_code.llm.client import NebiusNemotronClient
from aero_code.schemas.patch import PatchProposal


class PatchEngineerAgent:
    """Agent responsible for code patch synthesis and regression test generation."""

    def __init__(self, llm_client: Optional[NebiusNemotronClient] = None) -> None:
        self.llm_client = llm_client or NebiusNemotronClient()

    def create_patch(
        self,
        issue_title: str,
        source_code: str,
        research_context: str = "",
        escalate: bool = False,
        retry_error: str = "",
    ) -> PatchProposal:
        """Prompt NVIDIA Nemotron to generate surgical fix diffs and regression tests."""
        return self.llm_client.generate_patch(
            issue_title=issue_title,
            source_code=source_code,
            research_context=research_context,
            escalate=escalate,
            retry_error=retry_error,
        )
