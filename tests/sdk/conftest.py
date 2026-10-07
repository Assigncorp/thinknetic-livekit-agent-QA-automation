"""
Fixtures for the basic LiveKit SDK suite.

One event loop for the whole session (pyproject: asyncio_default_*_loop_scope),
because the LiveKit SDK binds its handles to the loop they were created on.
"""

from __future__ import annotations

import sys

sys.dont_write_bytecode = True

import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

os.environ.setdefault("AGENT_NAME", "thinknetic-agents-nonprod")


@pytest.fixture(scope="session")
def product() -> dict[str, str]:
    """The agent's product context - what the product backend's session endpoint
    puts in the dispatch metadata. Without it the agent joins and never speaks."""
    return {
        "product_name": os.getenv("PRODUCT_NAME", "Chip Spreader"),
        "product_brand": os.getenv("PRODUCT_BRAND", "Etnyre"),
        "organization_id": os.getenv("ORGANIZATION_ID", "11111111-1111-1111-1111-111111111111"),
        "organization_slug": os.getenv("ORG_SLUG", "e"),
        "knowledge_base_id": os.getenv("KNOWLEDGE_BASE_ID", "34456cd9-49ea-4d87-8edb-9a60b02e0321"),
        "assistant": os.getenv("ASSISTANT", "enterprises-product-support-assistant"),
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
