"""Configuration and environment settings using Pydantic Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global configuration settings for Aero-Code."""

    nebius_base_url: str = "https://api.tokenfactory.nebius.com/v1/"
    primary_model: str = "nvidia/Nemotron-3.5-Lightning"
    escalation_model: str = "nvidia/Nemotron-3-Ultra-550b-a55b"

    nebius_api_key: str = ""
    tavily_api_key: str = ""
    github_token: str = ""

    mode: str = "demo"  # "demo" or "live"
    timeout_seconds: int = 45
    max_retries: int = 3

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
