"""Ephemeral subprocess sandbox adapter with credential stripping and timeout enforcement."""

import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Dict, Optional

from aero_code.schemas.patch import PatchProposal
from aero_code.verifier.sandbox.base import BaseSandboxAdapter, SandboxExecutionResult


class SubprocessSandboxAdapter(BaseSandboxAdapter):
    """Executes test runs inside a local ephemeral temporary directory."""

    STRIPPED_ENV_VARS = [
        "NEBIUS_API_KEY",
        "TAVILY_API_KEY",
        "GITHUB_TOKEN",
        "OPENAI_API_KEY",
        "AWS_SECRET_ACCESS_KEY",
        "AZURE_OPENAI_API_KEY",
    ]

    def _build_clean_env(self, source_env: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Strip all sensitive credentials from the execution environment."""
        env = dict(source_env if source_env is not None else os.environ)
        for var in self.STRIPPED_ENV_VARS:
            env.pop(var, None)
        return env

    def _apply_patch(self, sandbox_dir: Path, patch: PatchProposal) -> None:
        """Apply patch diffs and write the regression test file in the sandbox."""
        for diff in patch.diffs:
            target_path = sandbox_dir / diff.file_path
            target_path.parent.mkdir(parents=True, exist_ok=True)
            # If new_content is provided, write it directly
            target_path.write_text(diff.new_content, encoding="utf-8")

        if patch.regression_test_code and patch.regression_test_file:
            test_path = sandbox_dir / patch.regression_test_file
            test_path.parent.mkdir(parents=True, exist_ok=True)
            test_path.write_text(patch.regression_test_code, encoding="utf-8")

    def run_test_suite(
        self,
        repo_root: str,
        test_target: Optional[str] = None,
        patch: Optional[PatchProposal] = None,
    ) -> SandboxExecutionResult:
        """Clone repo to tempdir, optionally apply patch, run pytest, and collect output."""
        start_time = time.perf_counter()

        with tempfile.TemporaryDirectory() as temp_dir:
            sandbox_path = Path(temp_dir) / "repo"
            # Copy source directory to sandbox ignoring caches and venvs
            shutil.copytree(
                repo_root,
                sandbox_path,
                ignore=shutil.ignore_patterns(
                    ".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".superpowers"
                ),
            )

            # Apply patch diffs if provided
            if patch is not None:
                self._apply_patch(sandbox_path, patch)

            clean_env = self._build_clean_env()
            # Ensure sandbox repo root and src/ are in PYTHONPATH
            existing_pythonpath = clean_env.get("PYTHONPATH", "")
            src_path = str(sandbox_path / "src")
            repo_str = str(sandbox_path)
            clean_env["PYTHONPATH"] = (
                f"{repo_str}{os.pathsep}{src_path}{os.pathsep}{existing_pythonpath}".strip(os.pathsep)
            )

            cmd = [sys.executable, "-m", "pytest", "-v"]
            if test_target:
                cmd.append(test_target)

            try:
                proc = subprocess.run(
                    cmd,
                    cwd=str(sandbox_path),
                    env=clean_env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=self.timeout_seconds,
                )
                duration_ms = (time.perf_counter() - start_time) * 1000.0
                return SandboxExecutionResult(
                    exit_code=proc.returncode,
                    stdout=proc.stdout,
                    stderr=proc.stderr,
                    duration_ms=duration_ms,
                    passed=(proc.returncode == 0),
                )
            except subprocess.TimeoutExpired as exc:
                duration_ms = (time.perf_counter() - start_time) * 1000.0
                stdout = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
                stderr = exc.stderr.decode() if isinstance(exc.stderr, bytes) else (exc.stderr or "")
                return SandboxExecutionResult(
                    exit_code=-1,
                    stdout=stdout,
                    stderr=f"Timeout expired after {self.timeout_seconds} seconds.\n{stderr}",
                    duration_ms=duration_ms,
                    passed=False,
                )
            except Exception as exc:
                duration_ms = (time.perf_counter() - start_time) * 1000.0
                return SandboxExecutionResult(
                    exit_code=-1,
                    stdout="",
                    stderr=str(exc),
                    duration_ms=duration_ms,
                    passed=False,
                )
