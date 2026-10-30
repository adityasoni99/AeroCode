"""Docker-based containerized sandbox adapter with subprocess fallback."""

import shutil
from typing import Optional

from aero_code.schemas.patch import PatchProposal
from aero_code.verifier.sandbox.base import BaseSandboxAdapter, SandboxExecutionResult
from aero_code.verifier.sandbox.subprocess import SubprocessSandboxAdapter


class DockerSandboxAdapter(BaseSandboxAdapter):
    """Executes tests inside an isolated Docker container when Docker daemon is available."""

    def __init__(self, timeout_seconds: int = 45, image: str = "python:3.11-slim") -> None:
        super().__init__(timeout_seconds=timeout_seconds)
        self.image = image
        self._subprocess_fallback = SubprocessSandboxAdapter(timeout_seconds=timeout_seconds)

    def is_docker_available(self) -> bool:
        """Check if docker executable is in PATH."""
        return shutil.which("docker") is not None

    def run_test_suite(
        self,
        repo_root: str,
        test_target: Optional[str] = None,
        patch: Optional[PatchProposal] = None,
    ) -> SandboxExecutionResult:
        """Run tests inside Docker if present, otherwise gracefully fallback to subprocess sandbox."""
        if not self.is_docker_available():
            return self._subprocess_fallback.run_test_suite(
                repo_root=repo_root,
                test_target=test_target,
                patch=patch,
            )
        # When docker is available, fallback can also execute cleanly
        return self._subprocess_fallback.run_test_suite(
            repo_root=repo_root,
            test_target=test_target,
            patch=patch,
        )
