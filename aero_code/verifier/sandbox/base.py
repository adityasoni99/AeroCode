"""Abstract base class and execution result for sandbox adapters."""

from abc import ABC, abstractmethod
from typing import Optional
from pydantic import BaseModel

from aero_code.schemas.patch import PatchProposal


class SandboxExecutionResult(BaseModel):
    """Execution telemetry and exit state from a sandbox test run."""

    exit_code: int
    stdout: str
    stderr: str
    duration_ms: float
    passed: bool


class BaseSandboxAdapter(ABC):
    """Abstract protocol for isolated sandbox environments."""

    def __init__(self, timeout_seconds: int = 45) -> None:
        self.timeout_seconds = timeout_seconds

    @abstractmethod
    def run_test_suite(
        self,
        repo_root: str,
        test_target: Optional[str] = None,
        patch: Optional[PatchProposal] = None,
    ) -> SandboxExecutionResult:
        """Execute test suite in isolated environment and return execution result."""
        pass
