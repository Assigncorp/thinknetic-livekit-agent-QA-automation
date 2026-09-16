"""
Thin client for the public product endpoints.

Tests should describe behaviour, not URL construction. Every path the suite
touches is built here, so a routing change is a one-file edit.
"""

from __future__ import annotations

import httpx


class ProductClient:
    def __init__(self, client: httpx.Client) -> None:
        self._client = client

    @staticmethod
    def product_path(org: str, slug: str) -> str:
        return f"/api/v1/public/organizations/{org}/products/{slug}"

    def get_product(self, org: str, slug: str) -> httpx.Response:
        return self._client.get(self.product_path(org, slug))

    def get_runtime_config(self) -> httpx.Response:
        """The SPA's /env.js - a config surface, not an API, but worth guarding."""
        return self._client.get("/env.js")
