"""The product claim in code: material is a filter, fusion is the identity."""

from app.search import search
from app.simulator import HomeSimulator


def _by_id(result, object_id):
    return next(hit for hit in result["hits"] if hit["id"] == object_id)


def test_fusion_picks_keys_over_other_metal():
    home = HomeSimulator()
    result = search(home, query="açarımı tap", mode="fusion", top_k=8)
    assert result["hits"][0]["id"] == "obj-keys"
    keys = _by_id(result, "obj-keys")
    spoon = _by_id(result, "obj-spoon")
    assert keys["confidence"] > spoon["confidence"] + 0.2
    assert keys["scores"]["category"] == 1.0
    assert spoon["scores"]["category"] == 0.0


def test_material_only_cannot_separate_key_from_spoon():
    home = HomeSimulator()
    result = search(home, query="açarımı tap", mode="material_only", top_k=8)
    keys = _by_id(result, "obj-keys")
    spoon = _by_id(result, "obj-spoon")
    assert keys["scores"]["material"] > 0.85
    assert spoon["scores"]["material"] > 0.75
    assert abs(keys["confidence"] - spoon["confidence"]) < 0.2
    assert result["warning"]


def test_wallet_is_found_in_bedroom():
    home = HomeSimulator()
    result = search(home, query="cüzdanımı tap", mode="fusion")
    assert result["hits"][0]["id"] == "obj-wallet"
    assert result["hits"][0]["room"] == "bedroom"
