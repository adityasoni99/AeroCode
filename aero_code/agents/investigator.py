"""Investigator Agent: Parses stack traces and diagnoses bug root causes via Nemotron."""

import re
from typing import Optional
from pydantic import BaseModel

from aero_code.llm.client import NebiusNemotronClient
from aero_code.schemas.issues import IssueReport, TracebackFrame


class InvestigationReport(BaseModel):
    """Detailed diagnosis of defect root cause, implicated symbol, and origin file."""

    implicated_symbol: str
    root_cause: str
    source_file: str = ""
    line_number: int = 0


class InvestigatorAgent:
    """Agent responsible for traceback extraction and root-cause localization."""

    def __init__(self, llm_client: Optional[NebiusNemotronClient] = None) -> None:
        self.llm_client = llm_client or NebiusNemotronClient()

    def parse_frames(self, traceback_str: str) -> list[TracebackFrame]:
        """Parse raw Python traceback string into structured frames."""
        frames: list[TracebackFrame] = []
        frame_pattern = re.compile(r'File "([^"]+)", line (\d+), in (\w+)\n\s*(.*)')
        for match in frame_pattern.finditer(traceback_str):
            frames.append(
                TracebackFrame(
                    file_path=match.group(1),
                    line_number=int(match.group(2)),
                    function_name=match.group(3),
                    code_line=match.group(4).strip(),
                )
            )
        return frames

    def analyze(self, issue: IssueReport, source_code: str = "") -> InvestigationReport:
        """Diagnose root cause and identify implicated symbol."""
        if issue.traceback and not issue.frames:
            issue.frames = self.parse_frames(issue.traceback)

        inv_res = self.llm_client.investigate(
            issue_title=issue.title,
            traceback=issue.traceback,
            source_code=source_code,
        )

        issue.implicated_symbol = inv_res.implicated_symbol
        issue.source_file = inv_res.source_file

        return InvestigationReport(
            implicated_symbol=inv_res.implicated_symbol,
            root_cause=inv_res.root_cause,
            source_file=inv_res.source_file,
            line_number=inv_res.line_number,
        )
