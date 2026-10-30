"""Baseline tests for requests_timeout_kwarg case — DO NOT MODIFY (Git Guard protected)."""
import inspect
from src.client import fetch_data


def test_fetch_data_is_callable():
    """Baseline: fetch_data must be a callable accepting a url argument."""
    sig = inspect.signature(fetch_data)
    assert "url" in sig.parameters
