"""
The SPA loads /env.js at runtime, so environment switching happens without a
rebuild. That makes it a config surface worth guarding: a dev build pointing at
prod (or vice versa) is exactly the kind of defect that ships quietly.
"""

import pytest


@pytest.mark.smoke
@pytest.mark.live
def test_env_js_is_served(client):
    r = client.get("/env.js")
    assert r.status_code == 200
    assert r.text.strip(), "/env.js was empty"


@pytest.mark.live
def test_env_js_does_not_leak_obvious_secrets(client):
    body = client.get("/env.js").text.lower()
    for needle in ("secret", "private_key", "password"):
        assert needle not in body, f"/env.js appears to expose '{needle}'"
