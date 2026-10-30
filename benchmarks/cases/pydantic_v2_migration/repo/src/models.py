"""User model using deprecated Pydantic V1 parse_obj API (bugged version)."""
from pydantic import BaseModel


class UserModel(BaseModel):
    id: int
    name: str


def parse_user(data: dict) -> UserModel:
    """Parse user data using deprecated Pydantic V1 API."""
    return UserModel.parse_obj(data)
