"""
Public product endpoint - the payload the SPA hydrates from.

No auth required, so this is the cheapest signal in the whole suite: if this
is wrong, every UI test downstream is testing the wrong data.

Contract confirmed against etnyre-dev on 2026-09-16.
"""

import pytest

# Fields the UI depends on. Kept deliberately short - asserting the whole
# payload turns every product-copy edit into a test failure.
REQUIRED_FIELDS = {
    "id",
    "organization_id",
    "name",
    "slug",
    "description",
    "has_assistant",
    "assets",
}


@pytest.fixture(scope="module")
def product(client, product_path) -> dict:
    r = client.get(product_path)
    assert r.status_code == 200, r.text
    return r.json()


@pytest.mark.smoke
@pytest.mark.live
def test_public_product_returns_200(client, product_path):
    r = client.get(product_path)
    assert r.status_code == 200, r.text
    assert "application/json" in r.headers.get("content-type", "")


@pytest.mark.smoke
@pytest.mark.live
def test_payload_contains_required_fields(product):
    missing = REQUIRED_FIELDS - set(product)
    assert not missing, f"missing required fields: {sorted(missing)}"


@pytest.mark.smoke
@pytest.mark.live
def test_product_advertises_an_assistant(product):
    """If this flips false, the 'Talk to me' entry point disappears from the UI."""
    assert product["has_assistant"] is True, "product no longer advertises an assistant"


@pytest.mark.live
def test_slug_matches_the_requested_product(product, product_path):
    assert product["slug"] == product_path.rsplit("/", 1)[-1]


@pytest.mark.live
def test_product_has_assets(product):
    assert product["assets"], "product returned no assets - the gallery will be empty"


@pytest.mark.live
def test_unknown_product_returns_404(client):
    r = client.get("/api/v1/public/organizations/e/products/definitely-not-a-real-product")
    assert r.status_code == 404
    assert set(r.json()) >= {"message", "statusCode"}


@pytest.mark.live
def test_unknown_organization_returns_404(client):
    r = client.get("/api/v1/public/organizations/zz-not-an-org/products/chip-spreader")
    assert r.status_code == 404


@pytest.mark.live
def test_response_time_within_budget(client, product_path):
    r = client.get(product_path)
    # Observed ~0.4s on dev. Budget set well above that; tighten once you have
    # a baseline spread rather than a single sample.
    assert r.elapsed.total_seconds() < 3.0, f"took {r.elapsed.total_seconds():.2f}s"
