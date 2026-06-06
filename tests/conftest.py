"""Shared test configuration and fixtures."""

import logging
from pathlib import Path

import pytest

TEST_DOCS_DIR = Path(__file__).parent.parent / "test_documents"
TEST_DOCS_SANITY = TEST_DOCS_DIR / "sanity"
TEST_DOCS_REAL = TEST_DOCS_DIR / "real"


def pytest_configure(config):
    """Set up logging once for all tests."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(message)s",
        datefmt="%H:%M:%S",
    )
