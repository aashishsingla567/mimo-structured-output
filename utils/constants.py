"""Shared constants for the mimo-structured-output project."""

from pathlib import Path

MAX_ATTEMPTS = 3
MAX_COMPLETION_TOKENS = 5120

REPO_ROOT = Path(__file__).parent.parent
PRICING_FILE = REPO_ROOT / "model_pricing.json"
REPORTS_FILE = REPO_ROOT / "reports.json"
