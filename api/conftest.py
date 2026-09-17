import json
import os
from pathlib import Path

import httpx
import pytest
from dotenv import load_dotenv

from src.clients.product_client import ProductClient

ROOT = Path(__file__).resolve().parents[1]

# Both toolchains read the same .env at the repo root.
load_dotenv(ROOT / ".env")

BASE_URL = os.getenv("BASE_URL", "https://etnyre-dev.thinknetic.app")
ORG_SLUG = os.getenv("ORG_SLUG", "e")
PRODUCT_SLUG = os.getenv("PRODUCT_SLUG", "chip-spreader")

# Slugs that must NOT exist, for the fail-closed checks.
UNKNOWN_ORG_SLUG = os.getenv("UNKNOWN_ORG_SLUG", "zz-not-an-org")
UNKNOWN_PRODUCT_SLUG = os.getenv("UNKNOWN_PRODUCT_SLUG", "definitely-not-a-real-product")


@pytest.fixture(scope="session")
def base_url() -> str:
    return BASE_URL.rstrip("/")


@pytest.fixture(scope="session")
def client(base_url: str):
    with httpx.Client(base_url=base_url, timeout=20.0, follow_redirects=True) as c:
        yield c


@pytest.fixture(scope="session")
def product_client(client) -> ProductClient:
    return ProductClient(client)


@pytest.fixture(scope="session")
def org_slug() -> str:
    return ORG_SLUG


@pytest.fixture(scope="session")
def product_slug() -> str:
    return PRODUCT_SLUG


@pytest.fixture(scope="session")
def unknown_org_slug() -> str:
    return UNKNOWN_ORG_SLUG


@pytest.fixture(scope="session")
def unknown_product_slug() -> str:
    return UNKNOWN_PRODUCT_SLUG


@pytest.fixture(scope="session")
def product_path(org_slug: str, product_slug: str) -> str:
    return ProductClient.product_path(org_slug, product_slug)


@pytest.fixture(scope="session")
def product_schema() -> dict:
    schema = Path(__file__).parent / "src" / "schemas" / "product.schema.json"
    return json.loads(schema.read_text(encoding="utf-8"))
