"""Real-photo enrollment and search.

This is still not YOLO/CLIP. A close-up reference photo is compared to the
current camera frame with color/spatial fingerprints over several crops.
Point the camera at the suspected object; a tiny key in a wide room shot
will often miss — that limit is shown in the UI.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .simulator import HomeSimulator, PhysicalObject
from .vision import (
    best_photo_match,
    fingerprint_from_bytes,
    load_rgb,
    material_cues_from_array,
)

FOUND = 0.82
MAYBE = 0.68


def data_dir() -> Path:
    override = os.environ.get("TAPAI_DATA")
    root = Path(override) if override else Path(__file__).resolve().parent.parent / "data"
    (root / "photos").mkdir(parents=True, exist_ok=True)
    return root


def photos_dir() -> Path:
    return data_dir() / "photos"


def seen_path() -> Path:
    return data_dir() / "last_seen.json"


def load_sightings() -> list[dict[str, Any]]:
    path = seen_path()
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def save_sightings(rows: list[dict[str, Any]]) -> None:
    seen_path().write_text(json.dumps(rows[:50], ensure_ascii=False, indent=2), encoding="utf-8")


def verdict_for(score: float) -> str:
    if score >= FOUND:
        return "found"
    if score >= MAYBE:
        return "maybe"
    return "miss"


def enroll_photo(home: HomeSimulator, item_id: str, photo: bytes) -> PhysicalObject:
    item = home.objects.get(item_id)
    if not item:
        raise KeyError(f"Əşya tapılmadı: {item_id}")
    item.photo_fp = fingerprint_from_bytes(photo)
    item.has_photo = True
    photos_dir().mkdir(parents=True, exist_ok=True)
    (photos_dir() / f"{item.id}.jpg").write_bytes(photo)
    return item


def record_sighting(
    item: PhysicalObject,
    score: float,
    lat: float | None,
    lon: float | None,
) -> dict[str, Any] | None:
    verdict = verdict_for(score)
    if verdict == "miss":
        return None
    row = {
        "item_id": item.id,
        "name": item.name,
        "score": round(score, 3),
        "verdict": verdict,
        "at": datetime.now(timezone.utc).isoformat(),
        "lat": lat,
        "lon": lon,
        "source": "camera",
        "room_az": item.public_dict()["room_az"],
    }
    rows = [row, *load_sightings()]
    save_sightings(rows)
    return row


def search_photo(
    home: HomeSimulator,
    photo: bytes,
    item_id: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
) -> dict[str, Any]:
    scene = load_rgb(photo)
    cues = material_cues_from_array(scene)
    if item_id:
        items = [home.objects[item_id]] if item_id in home.objects else []
        if not items:
            raise KeyError(f"Əşya tapılmadı: {item_id}")
    else:
        items = [obj for obj in home.enrolled_items() if getattr(obj, "has_photo", False)]

    hits: list[dict[str, Any]] = []
    sighting = None
    for item in items:
        fp = getattr(item, "photo_fp", None)
        if fp is None:
            hits.append(
                {
                    **item.public_dict(),
                    "score": 0.0,
                    "verdict": "no_photo",
                    "explanation": "Bu əşyanın referans fotosu yoxdur. Əvvəl yaxın planda tanıt.",
                }
            )
            continue
        score = float(best_photo_match(fp, scene))
        verdict = verdict_for(score)
        if verdict == "found":
            explanation = "Kadrdakı görünüş referans fotoya yaxındır."
        elif verdict == "maybe":
            explanation = "Oxşarlıq var, amma kadr geniş və ya işıq fərqlidir. Yaxınlaşdırıb yenə çək."
        else:
            explanation = "Bu kadrda tapılmadı. Kameranı əşyaya yaxın tut."
        payload = {
            **item.public_dict(),
            "score": round(score, 3),
            "verdict": verdict,
            "explanation": explanation,
        }
        hits.append(payload)
        if sighting is None and verdict != "miss":
            sighting = record_sighting(item, score, lat, lon)

    hits.sort(key=lambda row: row["score"], reverse=True)
    if hits:
        hits[0]["is_best"] = True

    return {
        "source": "camera",
        "physics_note": (
            "Bu, sənin çəkdiyin real şəkildir. Skor rəng və məkan izinin oxşarlığıdır, "
            "YOLO/CLIP deyil. Kiçik açar uzaq otaq kadrında tez-tez görünməz."
        ),
        "material_cues": cues,
        "hits": hits,
        "sighting": sighting,
        "last_seen": load_sightings()[:8],
    }
