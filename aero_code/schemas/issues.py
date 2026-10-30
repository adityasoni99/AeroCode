"""Issue report and traceback parsing data models."""

from typing import List, Optional
from pydantic import BaseModel, Field


class TracebackFrame(BaseModel):
    """A single frame from a Python traceback."""

    file_path: str
    line_number: int
    function_name: str
    code_line: str = ""


class IssueReport(BaseModel):
    """Structured representation of a bug report or issue to be fixed."""

    issue_id: str
    title: str
    description: str = ""
    traceback: str = ""
    target_package: str = ""
    package_version: str = ""
    frames: List[TracebackFrame] = Field(default_factory=list)
    implicated_symbol: str = ""
    source_file: str = ""
