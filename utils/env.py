"""Environment variable validation — T3-style startup validation.

All env vars are validated at import time. If any are missing or invalid,
the program crashes immediately with a clear error message.

Usage:
    from utils.env import env
    print(env.MIMO_API_KEY)
"""

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Validated environment variables. Crashes on import if invalid."""

    MIMO_API_KEY: str = Field(description="API key for MiMo LLM")
    MIMO_MODEL: str = Field(
        default="mimo-v2.5",
        description="Model to use for extraction",
    )
    MIMO_BASE_URL: str = Field(
        default="https://token-plan-sgp.xiaomimimo.com/v1",
        description="API base URL",
    )

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


# Validates at import time — crashes immediately if env vars are missing/invalid
env = Settings()
