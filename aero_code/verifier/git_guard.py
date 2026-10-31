"""Git Guard policy engine enforcing baseline test and configuration immutability."""

import os
import re
from pathlib import PurePath
from typing import List, Optional, Set
from pydantic import BaseModel, Field

from aero_code.schemas.patch import PatchProposal


class GitGuardViolation(Exception):
    """Raised or referenced when a patch violates immutability rules."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class GitGuardResult(BaseModel):
    """Audit result from Git Guard validation."""

    is_valid: bool
    violations: List[str] = Field(default_factory=list)


class GitGuard:
    """Enforces the ProofLoop immutability policy:
    1. Zero modifications to existing baseline test files.
    2. Zero modifications to protected build/CI/environment configuration files.
    3. New regression tests must follow designated regression test naming patterns.
    """

    PROTECTED_CONFIG_PATTERNS = [
        r"^pyproject\.toml$",
        r"^setup\.py$",
        r"^setup\.cfg$",
        r"^requirements.*\.txt$",
        r"^\.github/.*",
        r"^Dockerfile.*",
        r"^docker-compose.*",
        r"^tox\.ini$",
    ]

    def __init__(self, protected_config_patterns: Optional[List[str]] = None) -> None:
        self.protected_patterns = (
            protected_config_patterns or self.PROTECTED_CONFIG_PATTERNS
        )

    def _normalize_path(self, path: str) -> str:
        """Normalize file paths to forward-slash Unix style."""
        return PurePath(path).as_posix()

    def is_protected_config(self, file_path: str) -> bool:
        """Check if a file path is a protected configuration or CI file."""
        norm_path = self._normalize_path(file_path)
        base_name = os.path.basename(norm_path)

        for pattern in self.protected_patterns:
            if re.match(pattern, norm_path, re.IGNORECASE) or re.match(pattern, base_name, re.IGNORECASE):
                return True
        return False

    SSL_BYPASS_PATTERN = re.compile(r"\bverify\s*=\s*False\b", re.IGNORECASE)
    SECRET_LEAKAGE_PATTERN = re.compile(
        r"(?i)\b(client_secret|api_key|access_token|secret_key|webhook_secret|auth_token)\s*=\s*['\"][A-Za-z0-9_\-]{12,}['\"]"
    )

    def _check_security_violations(self, content: str, file_path: str) -> List[str]:
        """Check patch content for security and compliance violations."""
        security_violations = []
        if self.SSL_BYPASS_PATTERN.search(content):
            security_violations.append(
                f"SSL verification bypass (e.g. verify=False) is prohibited: {file_path}"
            )
        if self.SECRET_LEAKAGE_PATTERN.search(content):
            security_violations.append(
                f"Hardcoded credential or secret detected in patch: {file_path}"
            )
        return security_violations

    def validate(
        self,
        patch: PatchProposal,
        baseline_test_files: Optional[Set[str]] = None,
    ) -> GitGuardResult:
        """Validate that the proposed patch does not touch protected files, existing tests, or introduce security vulnerabilities."""
        violations: List[str] = []
        baseline_tests = {self._normalize_path(f) for f in (baseline_test_files or set())}

        # Check each file diff in the patch
        for diff in patch.diffs:
            norm_path = self._normalize_path(diff.file_path)

            # 1. Config protection rule
            if self.is_protected_config(norm_path):
                violations.append(
                    f"Modification of protected config file is prohibited: {diff.file_path}"
                )

            # 2. Immutable baseline test rule
            if norm_path in baseline_tests:
                violations.append(
                    f"Modification of immutable baseline test file is prohibited: {diff.file_path}"
                )
            elif norm_path.startswith("tests/") or norm_path.startswith("test/"):
                # Disallow modifying arbitrary existing tests via diff
                violations.append(
                    f"Modification of immutable baseline test file is prohibited: {diff.file_path}"
                )

            # 3. Security and payment compliance rules
            violations.extend(self._check_security_violations(diff.new_content, diff.file_path))

        # 4. Check regression test target file
        if patch.regression_test_file:
            norm_reg_file = self._normalize_path(patch.regression_test_file)
            if norm_reg_file in baseline_tests:
                violations.append(
                    f"Regression test cannot overwrite existing baseline test: {patch.regression_test_file}"
                )
            if patch.regression_test_code:
                violations.extend(
                    self._check_security_violations(
                        patch.regression_test_code, patch.regression_test_file
                    )
                )

        return GitGuardResult(
            is_valid=len(violations) == 0,
            violations=violations,
        )
