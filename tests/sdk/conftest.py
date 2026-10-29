"""
Fixtures for the basic LiveKit SDK suite.

One event loop for the whole session (pyproject: asyncio_default_*_loop_scope),
because the LiveKit SDK binds its handles to the loop they were created on.

Settings come from the section of .env that QA_ENV picks (lkqa/env.py).
"""

from __future__ import annotations

import sys

sys.dont_write_bytecode = True

import os

import pytest

from lkqa import env


def pytest_configure(config: pytest.Config) -> None:
    """Before any test module is imported: some read their settings at import time."""
    env.load()


@pytest.fixture(scope="session")
def product() -> dict[str, str]:
    """The agent's product context - what the product backend's session endpoint
    puts in the dispatch metadata. Without it the agent joins and never speaks."""
    return {
        "product_name": os.getenv("PRODUCT_NAME", ""),
        "product_brand": os.getenv("PRODUCT_BRAND", ""),
        "organization_id": os.getenv("ORGANIZATION_ID", ""),
        "organization_slug": os.getenv("ORG_SLUG", ""),
        "knowledge_base_id": os.getenv("KNOWLEDGE_BASE_ID", ""),
        "assistant": os.getenv("ASSISTANT", ""),
    }


@pytest.fixture(scope="session")
def caller() -> dict[str, str]:
    return {
        # The serial is set per call from kb/smoke_serials.yaml (lkqa.bank.choose).
        "serial": "",
        "name": os.getenv("TEST_CALLER_NAME", "Dale Hutchins"),
        "company": os.getenv("TEST_CALLER_COMPANY", "Fielder Paving"),
        "phone": os.getenv("TEST_CALLER_PHONE", "4805550142"),
    }
