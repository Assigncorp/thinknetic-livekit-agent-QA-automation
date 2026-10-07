"""
Schema contract for the public product payload.

Separate from the behavioural tests on purpose: when this file fails, the
backend changed its contract, and that is a different conversation from
"the endpoint is down".
"""

import pytest
from jsonschema import Draft202012Validator


@pytest.mark.smoke
@pytest.mark.live
def test_payload_matches_schema(product_client, org_slug, product_slug, product_schema):
    body = product_client.get_product(org_slug, product_slug).json()
    errors = sorted(Draft202012Validator(product_schema).iter_errors(body), key=lambda e: e.path)
    assert not errors, "\n".join(f"{list(e.path)}: {e.message}" for e in errors)
