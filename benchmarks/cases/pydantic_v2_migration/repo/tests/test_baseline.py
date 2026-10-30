"""Baseline tests for pydantic_v2_migration case — DO NOT MODIFY (Git Guard protected)."""
from src.models import UserModel


def test_user_model_fields():
    """Baseline: UserModel has required id and name fields."""
    user = UserModel(id=1, name="Alice")
    assert user.id == 1
    assert user.name == "Alice"
