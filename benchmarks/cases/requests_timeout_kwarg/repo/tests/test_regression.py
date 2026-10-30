"""Regression test for requests_timeout_kwarg — FAIL on bugged src, PASS on patched src."""
import ast
import inspect
from src.client import fetch_data


def test_fetch_data_has_timeout():
    """fetch_data source must include a timeout kwarg in the requests.get call."""
    source = inspect.getsource(fetch_data)
    tree = ast.parse(source)

    found_timeout = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            is_requests_get = (
                isinstance(func, ast.Attribute)
                and func.attr == "get"
            )
            if is_requests_get:
                kw_names = [kw.arg for kw in node.keywords]
                if "timeout" in kw_names:
                    found_timeout = True

    assert found_timeout, "requests.get() must include a timeout= keyword argument"
