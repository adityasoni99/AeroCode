import os
import subprocess
from pathlib import Path

import pytest

from aero_code.config import Settings
from aero_code.orchestrator.loop import ProofLoopOrchestrator
from aero_code.schemas.patch import FileDiff, PatchProposal
from aero_code.verifier.sandbox.docker import DockerSandboxAdapter
from aero_code.verifier.sandbox.subprocess import SubprocessSandboxAdapter


@pytest.fixture
def repo(tmp_path):
    root = tmp_path / "source repo"
    root.mkdir()
    (root / "test_example.py").write_text("def test_ok(): assert True\n")
    (root / ".env").write_text("SECRET=must-not-be-copied\n")
    (root / ".venv").mkdir()
    (root / ".venv" / "secret").write_text("ignored")
    return root


@pytest.fixture
def docker(monkeypatch):
    real_run = subprocess.run

    class DockerCLI:
        def __init__(self):
            self.commands = []
            self.workspace = None
            self.copied = {}
            self.exit_code = 0
            self.start_code = 0
            self.inspect_output = None
            self.advance = None
            self.fail = None
            self.timeout = None
            self.os_error = None
            self.available = True

        def run(self, cmd, **kwargs):
            if cmd[0] != "docker":
                return real_run(cmd, **kwargs)
            self.commands.append((cmd, kwargs))
            action = cmd[1]
            if self.advance:
                self.advance(action)
            if action == "create":
                mount = cmd[cmd.index("--mount") + 1]
                source = mount.split("source=", 1)[1].split(",target=", 1)[0]
                self.workspace = Path(source)
            if self.timeout == action:
                raise subprocess.TimeoutExpired(cmd, kwargs["timeout"], b"partial", b"details")
            if self.os_error == action:
                raise OSError(f"{action} unavailable")
            if self.fail == action:
                return subprocess.CompletedProcess(cmd, 1, "", f"{action} failed")
            if action == "info":
                return subprocess.CompletedProcess(cmd, 0 if self.available else 1, "", "daemon offline")
            if action == "create":
                self.copied = {
                    str(p.relative_to(self.workspace)): p.read_text()
                    for p in self.workspace.rglob("*") if p.is_file()
                }
                return subprocess.CompletedProcess(cmd, 0, "container-id\n", "")
            if action == "start":
                return subprocess.CompletedProcess(cmd, self.start_code, "pytest output\n", "pytest stderr\n")
            if action == "inspect":
                output = str(self.exit_code) if self.inspect_output is None else self.inspect_output
                return subprocess.CompletedProcess(cmd, 0, output, "")
            if action == "rm":
                return subprocess.CompletedProcess(cmd, 0, "container-id\n", "")
            raise AssertionError(f"Unexpected Docker action: {cmd}")

    fake = DockerCLI()
    monkeypatch.setattr("aero_code.verifier.sandbox.docker.shutil.which", lambda name: "docker")
    monkeypatch.setattr(subprocess, "run", fake.run)
    return fake


def test_docker_runs_isolated_tests_and_removes_workspace(repo, docker):
    result = DockerSandboxAdapter(timeout_seconds=90).run_test_suite(str(repo), "test_example.py")
    assert result.passed
    assert result.exit_code == 0
    assert result.stdout == "pytest output\n"
    assert result.stderr == "pytest stderr\n"
    assert result.duration_ms >= 0
    create = next(cmd for cmd, _ in docker.commands if cmd[1] == "create")
    for flag, value in (
        ("--cpus", "2"), ("--memory", "2g"), ("--memory-swap", "2g"),
        ("--network", "none"), ("--cap-drop", "ALL"),
        ("--security-opt", "no-new-privileges"), ("--pids-limit", "128"),
        ("--user", "65534:65534"), ("--pull", "never"),
    ):
        assert create[create.index(flag) + 1] == value
    assert "--read-only" in create
    assert "--init" in create
    assert "readonly" in create[create.index("--mount") + 1]
    assert create[-1] == "test_example.py"
    assert "--env" not in create
    assert ".env" not in docker.copied
    assert not any(".venv" in path for path in docker.copied)
    assert not docker.workspace.exists()
    assert [cmd[1] for cmd, _ in docker.commands] == ["info", "create", "start", "inspect", "rm"]
    assert all(0 < kw["timeout"] <= 60 for cmd, kw in docker.commands)


def test_docker_applies_patch_only_to_disposable_copy(repo, docker):
    proposal = PatchProposal(
        diffs=[FileDiff(file_path="module.py", old_content="", new_content="VALUE = 2\n")],
        regression_test_code="def test_regression(): assert True\n",
    )
    result = DockerSandboxAdapter().run_test_suite(str(repo), patch=proposal)
    assert result.passed
    assert docker.copied["module.py"] == "VALUE = 2\n"
    assert docker.copied[str(Path("tests") / "test_issue_regression.py")].startswith("def test")
    assert not (repo / "module.py").exists()


@pytest.mark.parametrize("path", ["../escaped.py", "/escaped.py", r"C:\escaped.py", r"..\escaped.py"])
def test_docker_rejects_escaping_patch_paths(repo, docker, path):
    proposal = PatchProposal(diffs=[FileDiff(file_path=path, old_content="", new_content="bad")])
    result = DockerSandboxAdapter().run_test_suite(str(repo), patch=proposal)
    assert not result.passed
    assert "path" in result.stderr.lower()
    assert not any(cmd[1] == "create" for cmd, _ in docker.commands)


@pytest.mark.parametrize("target", ["-x", "../outside.py", r"C:\outside.py", "/outside.py"])
def test_docker_rejects_unsafe_test_targets(repo, docker, target):
    result = DockerSandboxAdapter().run_test_suite(str(repo), target)
    assert not result.passed
    assert "target" in result.stderr.lower()
    assert not any(cmd[1] == "create" for cmd, _ in docker.commands)


def test_docker_unavailable_fails_closed(repo, docker):
    docker.available = False
    result = DockerSandboxAdapter().run_test_suite(str(repo))
    assert not result.passed
    assert "Docker" in result.stderr
    assert [cmd[1] for cmd, _ in docker.commands] == ["info"]


def test_missing_cli_fails_closed(repo, monkeypatch):
    monkeypatch.setattr("aero_code.verifier.sandbox.docker.shutil.which", lambda name: None)
    result = DockerSandboxAdapter().run_test_suite(str(repo))
    assert not result.passed
    assert "Docker" in result.stderr


@pytest.mark.parametrize("failure", ["timeout", "os_error"])
def test_daemon_probe_exception_fails_closed(repo, docker, failure):
    setattr(docker, failure, "info")
    result = DockerSandboxAdapter().run_test_suite(str(repo))
    assert not result.passed
    assert "Docker daemon unavailable" in result.stderr
    assert [cmd[1] for cmd, _ in docker.commands] == ["info"]


def test_explicit_fallback_runs_real_subprocess_with_warning(repo, monkeypatch, caplog):
    monkeypatch.setattr("aero_code.verifier.sandbox.docker.shutil.which", lambda name: None)
    result = DockerSandboxAdapter(allow_subprocess_fallback=True).run_test_suite(str(repo))
    assert result.passed
    assert "fallback" in caplog.text.lower()
    assert "isolation" in caplog.text.lower()


def test_unavailable_daemon_explicitly_falls_back(repo, monkeypatch, caplog):
    real_run = subprocess.run
    monkeypatch.setattr("aero_code.verifier.sandbox.docker.shutil.which", lambda name: "docker")

    def run(cmd, **kwargs):
        if cmd[0] == "docker":
            return subprocess.CompletedProcess(cmd, 1, "", "daemon offline")
        return real_run(cmd, **kwargs)

    monkeypatch.setattr(subprocess, "run", run)
    result = DockerSandboxAdapter(allow_subprocess_fallback=True).run_test_suite(str(repo))
    assert result.passed
    assert "daemon offline" in caplog.text
    assert "fallback" in caplog.text.lower()


@pytest.mark.parametrize("exit_code", [1, 2, 137])
def test_container_failure_is_not_retried_on_host(repo, docker, exit_code):
    docker.exit_code = exit_code
    result = DockerSandboxAdapter(allow_subprocess_fallback=True).run_test_suite(str(repo))
    assert not result.passed
    assert result.exit_code == exit_code
    assert result.stdout == "pytest output\n"
    assert docker.commands[-1][0][1] == "rm"


@pytest.mark.parametrize("action", ["create", "start", "inspect", "rm"])
def test_docker_lifecycle_errors_are_failures_with_cleanup(repo, docker, action):
    docker.fail = action
    result = DockerSandboxAdapter(allow_subprocess_fallback=True).run_test_suite(str(repo))
    assert not result.passed
    assert f"{action} failed" in result.stderr
    assert docker.commands[-1][0][1] == "rm"
    assert not docker.workspace.exists()


@pytest.mark.parametrize("action", ["create", "start", "inspect"])
def test_docker_timeout_force_removes_container(repo, docker, action):
    docker.timeout = action
    result = DockerSandboxAdapter(
        timeout_seconds=1, allow_subprocess_fallback=True
    ).run_test_suite(str(repo))
    assert not result.passed
    assert result.exit_code == -1
    assert "Timeout" in result.stderr
    assert "partial" in result.stdout
    assert "details" in result.stderr
    assert docker.commands[-1][0][1] == "rm"
    assert not docker.workspace.exists()


def test_attached_container_exit_status_is_preserved(repo, docker):
    docker.start_code = 1
    docker.exit_code = 1
    result = DockerSandboxAdapter(allow_subprocess_fallback=True).run_test_suite(str(repo))
    assert result.exit_code == 1
    assert result.stdout == "pytest output\n"
    assert result.stderr == "pytest stderr\n"
    assert not result.passed
    assert [cmd[1] for cmd, _ in docker.commands][-2:] == ["inspect", "rm"]


def test_shared_deadline_cannot_be_reset_between_lifecycle_steps(repo, docker, monkeypatch):
    clock = [0.0]
    monkeypatch.setattr("aero_code.verifier.sandbox.docker.time.perf_counter", lambda: clock[0])

    def advance(action):
        if action in ("create", "start"):
            clock[0] += 31

    docker.advance = advance
    result = DockerSandboxAdapter().run_test_suite(str(repo))
    assert not result.passed
    assert "Timeout" in result.stderr
    assert not any(cmd[1] == "inspect" for cmd, _ in docker.commands)
    start_timeout = next(kw["timeout"] for cmd, kw in docker.commands if cmd[1] == "start")
    assert start_timeout == 29
    assert docker.commands[-1][0][1] == "rm"


def test_invalid_container_exit_telemetry_is_failure(repo, docker):
    docker.inspect_output = "not-an-exit-code"
    result = DockerSandboxAdapter().run_test_suite(str(repo))
    assert not result.passed
    assert "error" in result.stderr.lower()
    assert docker.commands[-1][0][1] == "rm"


def test_cleanup_timeout_overrides_success(repo, docker, caplog):
    docker.timeout = "rm"
    result = DockerSandboxAdapter().run_test_suite(str(repo))
    assert not result.passed
    assert "cleanup failed" in result.stderr
    assert "cleanup failed" in caplog.text


@pytest.mark.parametrize("action", ["create", "start", "inspect", "rm"])
def test_cli_os_errors_are_explicit_failures(repo, docker, action):
    docker.os_error = action
    result = DockerSandboxAdapter(allow_subprocess_fallback=True).run_test_suite(str(repo))
    assert not result.passed
    assert f"{action} unavailable" in result.stderr
    assert docker.commands[-1][0][1] == "rm"


def test_patch_paths_are_validated_before_any_write(tmp_path):
    adapter = SubprocessSandboxAdapter()
    proposal = PatchProposal(diffs=[
        FileDiff(file_path="valid.py", old_content="", new_content="valid"),
        FileDiff(file_path="../escaped.py", old_content="", new_content="invalid"),
    ])
    with pytest.raises(ValueError, match="path"):
        adapter._apply_patch(tmp_path, proposal)
    assert not (tmp_path / "valid.py").exists()


def test_windows_relative_target_is_normalized_for_container(repo, docker):
    result = DockerSandboxAdapter().run_test_suite(str(repo), r"tests\test_ok.py::test_ok")
    assert result.passed
    create = next(cmd for cmd, _ in docker.commands if cmd[1] == "create")
    assert create[-1] == "tests/test_ok.py::test_ok"


def test_executable_source_permissions_are_preserved(repo, docker):
    script = repo / "run.sh"
    script.write_text("#!/bin/sh\nexit 0\n")
    script.chmod(0o755)
    observed = []

    def observe(action):
        if action == "start":
            observed.append((docker.workspace / "run.sh").stat().st_mode & 0o111)

    docker.advance = observe
    result = DockerSandboxAdapter().run_test_suite(str(repo))
    assert result.passed
    if os.name != "nt":
        assert observed == [0o111]


def test_source_symlink_is_not_followed(repo, docker, tmp_path):
    outside = tmp_path / "outside-secret"
    outside.write_text("not part of repository")
    try:
        (repo / "linked-secret").symlink_to(outside)
    except OSError:
        pytest.skip("Symlink creation requires Windows developer mode or privileges")
    result = DockerSandboxAdapter().run_test_suite(str(repo))
    assert result.passed
    assert "linked-secret" not in docker.copied


@pytest.mark.skipif(os.name != "nt", reason="Windows junctions are reparse points, not symlinks")
def test_source_junction_is_not_followed(repo, docker, tmp_path):
    outside = tmp_path / "private"
    outside.mkdir()
    (outside / "secret.txt").write_text("not part of repository")
    junction = repo / "linked-private"
    creation = subprocess.run(
        [
            "powershell", "-NoProfile", "-NonInteractive", "-Command",
            f"New-Item -ItemType Junction -Path '{junction}' -Target '{outside}' | Out-Null",
        ],
        capture_output=True, text=True, timeout=10,
    )
    assert creation.returncode == 0, creation.stderr
    result = DockerSandboxAdapter().run_test_suite(str(repo))
    assert result.passed
    assert not any("secret.txt" in path for path in docker.copied)


@pytest.mark.parametrize("timeout", [0, -1])
def test_invalid_timeout_is_rejected(timeout):
    with pytest.raises(ValueError, match="timeout"):
        DockerSandboxAdapter(timeout_seconds=timeout)


def test_live_orchestrator_uses_docker_and_demo_preserves_subprocess():
    live = ProofLoopOrchestrator(settings=Settings(_env_file=None), mode="live")
    demo = ProofLoopOrchestrator(settings=Settings(_env_file=None), mode="demo")
    assert isinstance(live.sandbox, DockerSandboxAdapter)
    assert isinstance(demo.sandbox, SubprocessSandboxAdapter)


def test_orchestrator_passes_image_and_explicit_fallback_settings():
    settings = Settings(
        _env_file=None, sandbox_image="custom-tests:local", sandbox_allow_subprocess_fallback=True
    )
    live = ProofLoopOrchestrator(settings=settings, mode="live")
    assert live.sandbox.image == "custom-tests:local"
    assert live.sandbox.allow_subprocess_fallback is True


@pytest.mark.skipif(
    os.environ.get("AERO_CODE_DOCKER_INTEGRATION") != "1",
    reason="Set AERO_CODE_DOCKER_INTEGRATION=1 with a prebuilt pytest image and running Docker",
)
def test_real_docker_isolation_and_patch(repo):
    (repo / "test_example.py").write_text(
        "import os, socket\n"
        "from pathlib import Path\n"
        "import pytest\n"
        "from module import VALUE\n"
        "def test_isolation():\n"
        "    assert VALUE == 2\n"
        "    assert os.getuid() == 65534\n"
        "    assert not Path('.env').exists()\n"
        "    assert 'NEBIUS_API_KEY' not in os.environ\n"
        "    with pytest.raises(OSError):\n"
        "        socket.create_connection(('1.1.1.1', 443), timeout=1)\n"
        "    with pytest.raises(OSError):\n"
        "        Path('/cannot-write').write_text('blocked')\n"
        "    cgroup = Path('/sys/fs/cgroup')\n"
        "    if (cgroup / 'memory.max').exists():\n"
        "        assert int((cgroup / 'memory.max').read_text()) == 2147483648\n"
        "        quota, period = (cgroup / 'cpu.max').read_text().split()\n"
        "        assert int(quota) / int(period) == 2\n"
        "    else:\n"
        "        assert int((cgroup / 'memory/memory.limit_in_bytes').read_text()) == 2147483648\n"
        "        cpu = cgroup / 'cpu'\n"
        "        assert int((cpu / 'cpu.cfs_quota_us').read_text()) / int((cpu / 'cpu.cfs_period_us').read_text()) == 2\n"
    )
    adapter = DockerSandboxAdapter(
        image=os.environ.get("AERO_CODE_DOCKER_IMAGE", "aero-code-sandbox:local")
    )
    proposal = PatchProposal(
        diffs=[FileDiff(file_path="module.py", old_content="", new_content="VALUE = 2\n")]
    )
    result = adapter.run_test_suite(str(repo), patch=proposal)
    assert result.passed, result.stderr + result.stdout
    assert not (repo / "module.py").exists()


@pytest.mark.skipif(
    os.environ.get("AERO_CODE_DOCKER_INTEGRATION") != "1",
    reason="Set AERO_CODE_DOCKER_INTEGRATION=1 with a prebuilt pytest image and running Docker",
)
@pytest.mark.parametrize("code,timeout,expected", [
    ("def test_failure(): assert False\n", 60, 1),
    ("import time\ndef test_hang(): time.sleep(120)\n", 3, -1),
])
def test_real_docker_failure_and_timeout(repo, code, timeout, expected):
    (repo / "test_example.py").write_text(code)
    adapter = DockerSandboxAdapter(
        timeout_seconds=timeout,
        image=os.environ.get("AERO_CODE_DOCKER_IMAGE", "aero-code-sandbox:local"),
    )
    result = adapter.run_test_suite(str(repo))
    assert not result.passed
    assert result.exit_code == expected, result.stdout + result.stderr
    if expected == -1:
        assert "Timeout" in result.stderr
        assert result.duration_ms < 10000
