"""
Public product endpoint - the payload the SPA hydrates from.

No auth required, so this is the cheapest signal in the whole suite: if this
is wrong, every UI test downstream is testing the wrong data.
"""

import pytest


@pytest.mark.smoke
@pytest.mark.live
def test_public_product_returns_200(client, product_path):
    r = client.get(product_path)
    assert r.status_code == 200, r.text


@pytest.mark.smoke
@pytest.mark.live
def test_public_product_returns_json(client, product_path):
    r = client.get(product_path)
    assert "application/json" in r.headers.get("content-type", "")
    assert isinstance(r.json(), (dict, list))


@pytest.mark.live
def test_public_product_payload_is_not_empty(client, product_path):
    body = client.get(product_path).json()
    assert body, "public product payload was empty"


@pytest.mark.live
def test_unknown_product_is_not_found(client):
    r = client.get("/api/v1/public/organizations/e/products/definitely-not-a-real-product")
    assert r.status_code in (400, 404), f"expected a client error, got {r.status_code}"


@pytest.mark.live
def test_unknown_organization_is_not_found(client):
    r = client.get("/api/v1/public/organizations/zz-not-an-org/products/chip-spreader")
    assert r.status_code in (400, 404), f"expected a client error, got {r.status_code}"


@pytest.mark.live
def test_response_time_within_budget(client, product_path):
    r = client.get(product_path)
    assert r.elapsed.total_seconds() < 3.0, f"took {r.elapsed.total_seconds():.2f}s"
