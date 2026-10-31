"""Abstract base class and execution result for sandbox adapters."""

from abc import ABC, abstractmethod
import shutil
import stat
from pathlib import Path, PureWindowsPath
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

    def _workspace_path(self, sandbox_dir: Path, file_path: str) -> Path:
        relative = Path(file_path.replace("\\", "/"))
        if (
            not file_path
            or relative.is_absolute()
            or PureWindowsPath(file_path).drive
            or ".." in relative.parts
        ):
            raise ValueError(f"Unsafe workspace path: {file_path!r}")
        target = (sandbox_dir / relative).resolve()
        if not target.is_relative_to(sandbox_dir.resolve()):
            raise ValueError(f"Workspace path escapes sandbox: {file_path!r}")
        return target

    def _apply_patch(self, sandbox_dir: Path, patch: PatchProposal) -> None:
        writes = [(diff.file_path, diff.new_content) for diff in patch.diffs]
        if patch.regression_test_code and patch.regression_test_file:
            writes.append((patch.regression_test_file, patch.regression_test_code))
        targets = [(self._workspace_path(sandbox_dir, path), content) for path, content in writes]
        for target, content in targets:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")

    def _prepare_workspace(self, repo_root: str, sandbox_dir: Path) -> None:
        def ignore(directory: str, names: list[str]) -> set[str]:
            excluded = set(shutil.ignore_patterns(
                ".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".superpowers",
                ".env", ".env.*",
            )(directory, names))
            for name in names:
                entry = Path(directory) / name
                attributes = getattr(entry.lstat(), "st_file_attributes", 0)
                if entry.is_symlink() or attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
                    excluded.add(name)
            return excluded

        shutil.copytree(repo_root, sandbox_dir, ignore=ignore)

    @abstractmethod
    def run_test_suite(
        self,
        repo_root: str,
        test_target: Optional[str] = None,
        patch: Optional[PatchProposal] = None,
    ) -> SandboxExecutionResult:
        """Execute test suite in isolated environment and return execution result."""
        pass
