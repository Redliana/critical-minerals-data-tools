"""Configuration for CMM API."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """API configuration settings."""

    # CLAIMM (EDX) settings
    edx_api_key: str = Field(default="", description="NETL EDX API Key")
    edx_base_url: str = Field(default="https://edx.netl.doe.gov/api/3/action")

    # BGS settings
    bgs_base_url: str = Field(
        default="https://ogcapi.bgs.ac.uk/collections/world-mineral-statistics"
    )

    # API settings
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
