"""Shared constants for the mimo-structured-output project."""

from pathlib import Path

DEFAULT_MODEL = "mimo-v2.5"
DEFAULT_BASE_URL = "https://token-plan-sgp.xiaomimimo.com/v1"
MAX_ATTEMPTS = 3
MAX_COMPLETION_TOKENS = 5120

ENV_API_KEY = "MIMO_API_KEY"
ENV_MODEL = "MIMO_MODEL"
ENV_BASE_URL = "MIMO_BASE_URL"

REPO_ROOT = Path(__file__).parent.parent
PRICING_FILE = REPO_ROOT / "model_pricing.json"
REPORTS_FILE = REPO_ROOT / "reports.json"
