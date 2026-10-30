"""Regression tests for pydantic_v2_migration — should FAIL on bugged src, PASS on patched src."""
from src.models import parse_user


def test_parse_user_regression():
    """parse_user must work without AttributeError."""
    result = parse_user({"id": 42, "name": "Bob"})
    assert result.id == 42
    assert result.name == "Bob"
