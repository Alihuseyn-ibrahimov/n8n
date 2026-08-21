"""Turn a query or item id into a ranked search result."""

from __future__ import annotations

from typing import Any

from .fusion import Target, rank
from .materials import AZ_FAMILY, AZ_MATERIAL, MATERIAL_FAMILIES, PROTOTYPES
from .nlp import CATEGORIES, parse_query
from .simulator import HomeSimulator, PhysicalObject
from .vision import visual_fingerprint

MODE_WARNINGS = {
    "material_only": (
        "Yalnız material: eyni sinifdən olan bütün əşyalar (məs. bütün metallar) "
        "yüksək skor alır. Bu, sənin açarını qaşıqdan ayırmır."
    ),
    "tag_only": "Yalnız tag: tag-i olmayan əşyalar görünməyəcək.",
    "visual_only": "Yalnız vizual iz: işıq və oxşar rəngli əşyalar çaşdıra bilər.",
}


def target_from_item(item: PhysicalObject) -> Target:
    return Target(
        name=item.name,
        category=item.category,
        material=item.material,
        spectrum=item.spectrum,
        visual=item.visual,
        tag_id=item.tag_id,
    )


def target_from_category(category: str) -> Target:
    meta = CATEGORIES[category]
    material = meta["default_material"]
    color = {
        "keys": (196, 148, 58),
        "wallet": (92, 48, 28),
        "phone": (40, 44, 52),
        "remote": (32, 32, 36),
        "glasses": (28, 30, 34),
        "headphones": (220, 220, 220),
        "watch": (192, 196, 200),
        "card": (200, 200, 210),
    }.get(category, (120, 120, 120))
    return Target(
        name=meta["az"],
        category=category,
        material=material,
        spectrum=PROTOTYPES[material].copy(),
        visual=visual_fingerprint(color, category),
        tag_id=None,
    )


def resolve_target(home: HomeSimulator, query: str | None, item_id: str | None) -> tuple[Target, PhysicalObject | None, str]:
    if item_id:
        item = home.objects.get(item_id)
        if not item:
            raise KeyError(f"Əşya tapılmadı: {item_id}")
        return target_from_item(item), item, query or item.name

    parsed = parse_query(query or "")
    if parsed.category:
        for item in home.enrolled_items():
            if item.category == parsed.category:
                return target_from_item(item), item, parsed.raw
        return target_from_category(parsed.category), None, parsed.raw

    raise ValueError("Sorğunu başa düşmədim. Məsələn: “açarımı tap” və ya siyahıdan əşya seç.")


def search(
    home: HomeSimulator,
    query: str | None = None,
    item_id: str | None = None,
    mode: str = "fusion",
    top_k: int = 5,
) -> dict[str, Any]:
    target, enrolled, display_query = resolve_target(home, query, item_id)
    detections = home.scan()
    hits = rank(target, detections, mode=mode)[:top_k]
    family = MATERIAL_FAMILIES[target.material]
    payload_hits = []
    for hit in hits:
        payload_hits.append(
            {
                **hit.obj.public_dict(),
                "confidence": round(hit.confidence, 3),
                "scores": {
                    "material": round(hit.material_score, 3),
                    "visual": round(hit.visual_score, 3),
                    "category": round(hit.category_score, 3),
                    "tag": round(hit.tag_score, 3),
                },
                "explanation": hit.explanation,
                "is_best": False,
            }
        )
    if payload_hits:
        payload_hits[0]["is_best"] = True

    return {
        "query": display_query,
        "mode": mode,
        "target": {
            "name": target.name,
            "category": target.category,
            "category_az": CATEGORIES.get(target.category, {}).get("az", target.category),
            "material": target.material,
            "material_az": AZ_MATERIAL[target.material],
            "family": family,
            "family_az": AZ_FAMILY[family],
            "has_tag": bool(target.tag_id),
            "enrolled_id": enrolled.id if enrolled else None,
        },
        "hits": payload_hits,
        "heatmap": home.metal_heatmap(),
        "warning": MODE_WARNINGS.get(mode),
        "physics_note": (
            "Material spektri eyni ailədəki əşyaları yaxınlaşdırır. "
            "Unikal tapıntı üçün forma, vizual iz və/və ya tag lazımdır."
        ),
    }
