"""kb/images.yaml and how a run picks the image it asks for. Offline."""

from __future__ import annotations

import pytest
import yaml

from lkqa import bank
from lkqa.kbcall import _same_image
from lkqa.routing import KB_FILES

pytestmark = pytest.mark.offline

PRODUCTS = yaml.safe_load(bank.IMAGES.read_text(encoding="utf-8"))["products"]


def test_every_product_is_a_known_model_with_images():
    for p in PRODUCTS:
        assert set(p["models"]) <= set(KB_FILES)
        assert p["images"], f"{p['models']} lists no images"


def test_every_smoke_model_has_an_image_list():
    for model in bank.SMOKE_MODELS:
        assert bank.load_images(model), f"{model} has no image list - its calls could not ask for an image"


@pytest.mark.parametrize("product", PRODUCTS, ids=["+".join(p["models"]) for p in PRODUCTS])
def test_images_have_unique_ids_and_descriptions(product):
    ids = [i["id"] for i in product["images"]]
    names = [i["description"].strip().lower() for i in product["images"]]
    assert all(names), "an image has no description - the caller could not ask for it"
    assert len(ids) == len(set(ids))
    assert len(names) == len(set(names)), "two images share a description - the check could not tell them apart"


def test_smoke_models_are_the_fixed_hopper_ones():
    assert set(bank.SMOKE_MODELS) == {"FHRC28", "FHRC36"}
    for seed in range(20):
        assert bank.choose(seed).model in bank.SMOKE_MODELS


def test_same_seed_same_image(monkeypatch):
    monkeypatch.delenv("KB_IMAGE", raising=False)
    assert bank.choose_image("FHRC28", 42) == bank.choose_image("FHRC28", 42)


def test_image_pin_by_description_or_id(monkeypatch):
    image = bank.load_images("FHRC28")[0]
    monkeypatch.setenv("KB_IMAGE", image["description"].upper())
    assert bank.choose_image("FHRC28", 1) == image
    monkeypatch.setenv("KB_IMAGE", image["id"])
    assert bank.choose_image("FHRC28", 1) == image
    monkeypatch.setenv("KB_IMAGE", "no such image")
    with pytest.raises(LookupError):
        bank.choose_image("FHRC28", 1)


def test_model_without_an_image_list_gets_none(monkeypatch):
    monkeypatch.delenv("KB_IMAGE", raising=False)
    listed = {m for p in PRODUCTS for m in p["models"]}
    for model in set(KB_FILES) - listed:
        assert bank.choose_image(model, 1) is None


def test_received_image_matches_on_description():
    wanted = {"description": "Pressure over-ride (POR) adjustment"}
    assert _same_image({"description": "pressure over-ride (POR) adjustment "}, wanted)
    assert not _same_image({"description": "Charge pressure adjustment"}, wanted)
    assert not _same_image({}, wanted)
