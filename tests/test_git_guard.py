# tests/test_git_guard.py
from aero_code.schemas.patch import PatchProposal, FileDiff
from aero_code.verifier.git_guard import GitGuard, GitGuardViolation

def test_git_guard_allows_valid_patch_and_new_regression_test():
    guard = GitGuard()
    patch = PatchProposal(
        diffs=[FileDiff(file_path="src/service.py", old_content="old", new_content="new")],
        regression_test_code="def test_fix_regression(): assert True",
        regression_test_file="tests/test_issue_101_regression.py"
    )
    result = guard.validate(patch, baseline_test_files={"tests/test_baseline.py"})
    assert result.is_valid is True
    assert len(result.violations) == 0

def test_git_guard_rejects_modification_of_existing_tests():
    guard = GitGuard()
    patch = PatchProposal(
        diffs=[
            FileDiff(file_path="tests/test_baseline.py", old_content="assert x == 1", new_content="assert True")
        ],
        regression_test_code="def test_fix_regression(): assert True",
        regression_test_file="tests/test_issue_101_regression.py"
    )
    result = guard.validate(patch, baseline_test_files={"tests/test_baseline.py"})
    assert result.is_valid is False
    assert any("immutable baseline test" in v.lower() for v in result.violations)

def test_git_guard_rejects_modification_of_build_configs():
    guard = GitGuard()
    patch = PatchProposal(
        diffs=[FileDiff(file_path="pyproject.toml", old_content="version = 1", new_content="version = 2")],
        regression_test_code="def test_fix_regression(): assert True"
    )
    result = guard.validate(patch, baseline_test_files=set())
    assert result.is_valid is False
    assert any("config file" in v.lower() for v in result.violations)


def test_git_guard_rejects_ssl_verification_bypass():
    guard = GitGuard()
    patch = PatchProposal(
        diffs=[
            FileDiff(
                file_path="src/client.py",
                old_content="requests.get(url)",
                new_content="requests.get(url, verify=False)",
            )
        ],
        regression_test_code="def test_ssl_regression(): assert True",
        regression_test_file="tests/test_ssl_regression.py",
    )
    result = guard.validate(patch, baseline_test_files=set())
    assert result.is_valid is False
    assert any("ssl verification bypass" in v.lower() for v in result.violations)


def test_git_guard_rejects_hardcoded_secrets():
    guard = GitGuard()
    patch = PatchProposal(
        diffs=[
            FileDiff(
                file_path="src/config.py",
                old_content="client_secret = os.getenv('SECRET')",
                new_content="client_secret = 'A21AAJsd87123981273981723912'",
            )
        ],
        regression_test_code="def test_secret_regression(): assert True",
        regression_test_file="tests/test_secret_regression.py",
    )
    result = guard.validate(patch, baseline_test_files=set())
    assert result.is_valid is False
    assert any("secret" in v.lower() or "credential" in v.lower() for v in result.violations)
