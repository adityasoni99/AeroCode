# tests/test_sandbox_runner.py
import os
import tempfile
from pathlib import Path
from aero_code.verifier.sandbox.subprocess import SubprocessSandboxAdapter
from aero_code.schemas.patch import PatchProposal, FileDiff

def test_sandbox_copies_and_executes_pytest():
    with tempfile.TemporaryDirectory() as src_dir:
        src_path = Path(src_dir)
        (src_path / "src").mkdir()
        (src_path / "tests").mkdir()
        (src_path / "src" / "math_lib.py").write_text("def add(a, b): return a + b\n")
        (src_path / "tests" / "test_add.py").write_text("from src.math_lib import add\ndef test_add(): assert add(1, 2) == 3\n")

        adapter = SubprocessSandboxAdapter(timeout_seconds=15)
        res = adapter.run_test_suite(repo_root=str(src_path), test_target="tests/test_add.py")
        assert res.exit_code == 0
        assert res.passed is True

def test_sandbox_strips_api_keys():
    adapter = SubprocessSandboxAdapter(timeout_seconds=5)
    env = adapter._build_clean_env({"NEBIUS_API_KEY": "secret-key", "PATH": "some-path"})
    assert "NEBIUS_API_KEY" not in env
    assert "TAVILY_API_KEY" not in env
    assert "GITHUB_TOKEN" not in env
    assert "PATH" in env
