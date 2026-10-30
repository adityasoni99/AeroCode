"""HTTP client missing timeout kwarg (bugged version)."""
import requests


def fetch_data(url: str) -> dict:
    """Fetch data from a URL — BUG: missing timeout may hang indefinitely."""
    response = requests.get(url)  # noqa: S113 — no timeout!
    response.raise_for_status()
    return response.json()
