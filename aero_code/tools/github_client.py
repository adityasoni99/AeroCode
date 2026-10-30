"""GitHub client for publishing verified fixes as Draft Pull Requests."""

import os
from typing import Any, Dict, Optional
import httpx

from aero_code.config import Settings


class GitHubClient:
    """Creates GitHub draft pull requests with embedded Evidence Reports."""

    def __init__(self, token: Optional[str] = None) -> None:
        settings = Settings()
        self.token = token or settings.github_token or os.environ.get("GITHUB_TOKEN", "")

    def create_draft_pr(
        self,
        repo: str,
        title: str,
        body: str,
        head_branch: str,
        base_branch: str = "main",
    ) -> Dict[str, Any]:
        """Create a draft PR on GitHub or return a mock record if no token is configured."""
        if not self.token:
            return {
                "pr_number": 42,
                "url": f"https://github.com/{repo}/pull/42",
                "title": title,
                "draft": True,
                "mock": True,
            }

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json",
        }
        payload = {
            "title": title,
            "body": body,
            "head": head_branch,
            "base": base_branch,
            "draft": True,
        }
        url = f"https://api.github.com/repos/{repo}/pulls"
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(url, json=payload, headers=headers)
                if resp.status_code == 201:
                    data = resp.json()
                    return {
                        "pr_number": data.get("number"),
                        "url": data.get("html_url"),
                        "title": title,
                        "draft": True,
                        "mock": False,
                    }
                else:
                    return {
                        "pr_number": 0,
                        "url": "",
                        "error": resp.text,
                        "status_code": resp.status_code,
                        "mock": False,
                    }
        except Exception as exc:
            return {
                "pr_number": 0,
                "url": "",
                "error": str(exc),
                "mock": False,
            }
