"""Disposable Docker execution with explicit, unavailable-only host fallback."""

import logging
import shutil
import subprocess
import tempfile
import time
import uuid
from pathlib import Path
from typing import Optional

from aero_code.schemas.patch import PatchProposal
from aero_code.verifier.sandbox.base import BaseSandboxAdapter, SandboxExecutionResult
from aero_code.verifier.sandbox.subprocess import SubprocessSandboxAdapter

logger = logging.getLogger(__name__)


class DockerSandboxAdapter(BaseSandboxAdapter):
    """Executes tests inside an isolated Docker container when Docker daemon is available."""

    def __init__(
        self,
        timeout_seconds: int = 60,
        image: str = "aero-code-sandbox:local",
        allow_subprocess_fallback: bool = False,
    ) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        super().__init__(timeout_seconds=min(timeout_seconds, 60))
        self.image = image
        self.allow_subprocess_fallback = allow_subprocess_fallback
        self._availability_error = ""
        self._subprocess_fallback = SubprocessSandboxAdapter(timeout_seconds=self.timeout_seconds)

    def is_docker_available(self) -> bool:
        """Probe both the CLI and daemon without pulling or running an image."""
        if shutil.which("docker") is None:
            self._availability_error = "Docker executable is not available."
            return False
        try:
            probe = subprocess.run(
                ["docker", "info", "--format", "{{.ServerVersion}}"],
                capture_output=True, text=True, timeout=5,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            self._availability_error = f"Docker daemon unavailable: {exc}"
            return False
        if probe.returncode != 0:
            self._availability_error = f"Docker daemon unavailable: {probe.stderr.strip()}"
            return False
        self._availability_error = ""
        return True

    @staticmethod
    def _output(value: str | bytes | None) -> str:
        return value.decode(errors="replace") if isinstance(value, bytes) else (value or "")

    def run_test_suite(
        self,
        repo_root: str,
        test_target: Optional[str] = None,
        patch: Optional[PatchProposal] = None,
    ) -> SandboxExecutionResult:
        """Execute pytest offline; never retry failed container execution on the host."""
        start_time = time.perf_counter()
        if not self.is_docker_available():
            if self.allow_subprocess_fallback:
                logger.warning(
                    "%s Subprocess fallback enabled: host execution has no container isolation.",
                    self._availability_error,
                )
                return self._subprocess_fallback.run_test_suite(
                    repo_root=repo_root, test_target=test_target, patch=patch,
                )
            return SandboxExecutionResult(
                exit_code=-1, stdout="", stderr=self._availability_error,
                duration_ms=(time.perf_counter() - start_time) * 1000, passed=False,
            )

        deadline = start_time + self.timeout_seconds
        stdout, stderr, exit_code = "", "", -1
        name = f"aero-code-sandbox-{uuid.uuid4().hex}"
        create_attempted = False

        def run_cli(args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
            remaining = deadline - time.perf_counter()
            if remaining <= 0:
                raise subprocess.TimeoutExpired(args, self.timeout_seconds)
            proc = subprocess.run(args, capture_output=True, text=True, timeout=remaining)
            if check and proc.returncode != 0:
                raise subprocess.CalledProcessError(
                    proc.returncode, args, output=proc.stdout, stderr=proc.stderr
                )
            return proc

        with tempfile.TemporaryDirectory(prefix="aero-docker-") as temp_dir:
            workspace = Path(temp_dir) / "repo"
            try:
                if test_target:
                    path = test_target.split("::", 1)[0]
                    if path.startswith("-"):
                        raise ValueError(f"Unsafe test target: {test_target!r}")
                    try:
                        self._workspace_path(workspace, path)
                    except ValueError as exc:
                        raise ValueError(f"Unsafe test target: {test_target!r}") from exc
                    test_target = test_target.replace("\\", "/")
                self._prepare_workspace(repo_root, workspace)
                if patch is not None:
                    self._apply_patch(workspace, patch)
                # Docker's unprivileged user must be able to read the staged source on Linux.
                Path(temp_dir).chmod(0o755)
                for entry in [workspace, *workspace.rglob("*")]:
                    entry.chmod(0o755 if entry.is_dir() else 0o644 | (entry.stat().st_mode & 0o111))
                script = (
                    "import os, shutil, sys; "
                    "shutil.copytree('/source', '/workspace/repo'); "
                    "os.chdir('/workspace/repo'); "
                    "os.environ['PYTHONPATH']='/workspace/repo:/workspace/repo/src'; "
                    "os.execv(sys.executable, [sys.executable, '-m', 'pytest', '-v', "
                    "'--', *sys.argv[1:]])"
                )
                command = [
                    "docker", "create", "--name", name, "--pull", "never",
                    "--cpus", "2", "--memory", "2g", "--memory-swap", "2g",
                    "--network", "none", "--ipc", "none", "--cap-drop", "ALL",
                    "--security-opt", "no-new-privileges", "--pids-limit", "128",
                    "--user", "65534:65534", "--read-only", "--init",
                    "--tmpfs", "/workspace:rw,nosuid,nodev,size=512m,mode=1777",
                    "--tmpfs", "/tmp:rw,nosuid,nodev,size=64m,mode=1777",
                    "--mount", f"type=bind,source={workspace},target=/source,readonly",
                    "--workdir", "/workspace", "--entrypoint", "python",
                    self.image, "-c", script,
                ]
                if test_target:
                    command.append(test_target)
                create_attempted = True
                run_cli(command)
                execution = run_cli(["docker", "start", "--attach", name], check=False)
                stdout, stderr = execution.stdout, execution.stderr
                state = run_cli(["docker", "inspect", "--format", "{{.State.ExitCode}}", name])
                exit_code = int(state.stdout.strip())
                if execution.returncode != 0 and exit_code == 0:
                    exit_code = -1
                    stderr = f"Docker start failed: {stderr}"
            except subprocess.TimeoutExpired as exc:
                stdout += self._output(exc.stdout)
                stderr += (
                    f"Timeout expired after {self.timeout_seconds} seconds.\n"
                    + self._output(exc.stderr)
                )
            except subprocess.CalledProcessError as exc:
                stdout += self._output(exc.output)
                stderr += f"Docker {exc.cmd[1]} failed: {self._output(exc.stderr)}"
            except (OSError, ValueError) as exc:
                stderr += f"Docker sandbox error: {exc}"
            finally:
                # Use the generated name even if create timed out after creating the container.
                if create_attempted:
                    try:
                        cleanup = subprocess.run(
                            ["docker", "rm", "--force", "--volumes", name],
                            capture_output=True, text=True, timeout=5,
                        )
                        if cleanup.returncode != 0 and not (
                            exit_code == -1 and "No such container" in cleanup.stderr
                        ):
                            exit_code = -1
                            stderr += f"\nDocker rm failed: {cleanup.stderr}"
                            logger.error("Container cleanup failed for %s: %s", name, cleanup.stderr)
                    except (OSError, subprocess.TimeoutExpired) as exc:
                        exit_code = -1
                        stderr += f"\nDocker cleanup failed for {name}: {exc}"
                        logger.error("Container cleanup failed for %s: %s", name, exc)
        return SandboxExecutionResult(
            exit_code=exit_code, stdout=stdout, stderr=stderr,
            duration_ms=(time.perf_counter() - start_time) * 1000,
            passed=exit_code == 0,
        )
