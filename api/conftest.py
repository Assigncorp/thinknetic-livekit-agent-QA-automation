import os
from pathlib import Path

import httpx
import pytest
from dotenv import load_dotenv

# Both toolchains read the same .env at the repo root.
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

BASE_URL = os.getenv("BASE_URL", "https://etnyre-dev.thinknetic.app")
ORG_SLUG = os.getenv("ORG_SLUG", "e")
PRODUCT_SLUG = os.getenv("PRODUCT_SLUG", "chip-spreader")


@pytest.fixture(scope="session")
def base_url() -> str:
    return BASE_URL.rstrip("/")


@pytest.fixture(scope="session")
def client(base_url: str):
    with httpx.Client(base_url=base_url, timeout=20.0, follow_redirects=True) as c:
        yield c


@pytest.fixture(scope="session")
def product_path() -> str:
    return f"/api/v1/public/organizations/{ORG_SLUG}/products/{PRODUCT_SLUG}"
