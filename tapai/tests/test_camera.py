from io import BytesIO

import numpy as np
import pytest
from PIL import Image

from app.camera import enroll_photo, search_photo, verdict_for
from app.simulator import HomeSimulator
from app.vision import best_photo_match, fingerprint_from_bytes


def jpeg_color(rgb: tuple[int, int, int], size: tuple[int, int] = (80, 80)) -> bytes:
    image = Image.new("RGB", size, rgb)
    buf = BytesIO()
    image.save(buf, format="JPEG", quality=92)
    return buf.getvalue()


@pytest.fixture
def data_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("TAPAI_DATA", str(tmp_path))
    return tmp_path


def test_same_photo_is_a_strong_match(data_dir):
    red = jpeg_color((200, 40, 40))
    score = best_photo_match(fingerprint_from_bytes(red), np.asarray(Image.open(BytesIO(red)).convert("RGB")))
    assert score > 0.95


def test_red_does_not_match_blue_as_well_as_itself(data_dir):
    home = HomeSimulator()
    red = jpeg_color((200, 30, 30))
    blue = jpeg_color((30, 30, 200))
    enroll_photo(home, "obj-keys", red)
    hit_red = search_photo(home, red, item_id="obj-keys")["hits"][0]
    hit_blue = search_photo(home, blue, item_id="obj-keys")["hits"][0]
    assert hit_red["verdict"] == "found"
    assert hit_red["score"] > hit_blue["score"] + 0.15
    assert hit_blue["verdict"] in {"miss", "maybe"}


def test_verdict_thresholds():
    assert verdict_for(0.9) == "found"
    assert verdict_for(0.7) == "maybe"
    assert verdict_for(0.2) == "miss"


def test_camera_api_enroll_and_search(data_dir):
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    red = jpeg_color((190, 25, 25))
    res = client.post("/api/items/obj-keys/photo", files={"photo": ("keys.jpg", red, "image/jpeg")})
    assert res.status_code == 200
    assert res.json()["has_photo"] is True
    found = client.post(
        "/api/camera/search",
        files={"photo": ("frame.jpg", red, "image/jpeg")},
        data={"item_id": "obj-keys"},
    )
    assert found.status_code == 200
    assert found.json()["hits"][0]["verdict"] == "found"


def test_search_without_reference_photo(data_dir):
    home = HomeSimulator()
    result = search_photo(home, jpeg_color((10, 10, 10)), item_id="obj-keys")
    assert result["hits"][0]["verdict"] == "no_photo"
