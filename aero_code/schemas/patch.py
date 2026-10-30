"""Patch proposals, file diffs, and regression test data models."""

from typing import List
from pydantic import BaseModel, Field


class FileDiff(BaseModel):
    """Unified or structured diff for a single file modification."""

    file_path: str
    old_content: str
    new_content: str


class PatchProposal(BaseModel):
    """A proposed patch composed of file diffs and an isolated regression test."""

    diffs: List[FileDiff] = Field(default_factory=list)
    regression_test_code: str = ""
    regression_test_file: str = "tests/test_issue_regression.py"
    explanation: str = ""
