"""Fuse material, visual, category and tag scores into one ranking.

Weights are intentionally visible: the UI can switch modes so a user sees why
material-only search lights up every metal object in the house.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .materials import MATERIAL_FAMILIES, cosine
from .simulator import PhysicalObject
from .vision import visual_similarity

MODES = {
    "fusion": {"material": 0.28, "visual": 0.32, "category": 0.25, "tag": 0.15},
    "material_only": {"material": 1.0, "visual": 0.0, "category": 0.0, "tag": 0.0},
    "visual_only": {"material": 0.0, "visual": 1.0, "category": 0.0, "tag": 0.0},
    "tag_only": {"material": 0.0, "visual": 0.0, "category": 0.0, "tag": 1.0},
}


@dataclass
class Target:
    name: str
    category: str
    material: str
    spectrum: np.ndarray
    visual: np.ndarray
    tag_id: str | None = None


@dataclass
class Hit:
    obj: PhysicalObject
    material_score: float
    visual_score: float
    category_score: float
    tag_score: float
    confidence: float
    explanation: str


def _category_score(target: Target, obj: PhysicalObject) -> float:
    if not target.category:
        return 0.0
    return 1.0 if obj.category == target.category else 0.0


def _tag_score(target: Target, obj: PhysicalObject) -> float:
    if target.tag_id and obj.tag_id == target.tag_id:
        return 1.0
    if target.tag_id and obj.tag_id:
        return 0.05
    return 0.0


def _explain(target: Target, obj: PhysicalObject, scores: dict[str, float], mode: str) -> str:
    family_t = MATERIAL_FAMILIES.get(target.material, "")
    family_o = MATERIAL_FAMILIES.get(obj.material, "")
    bits: list[str] = []
    if scores["material"] >= 0.8:
        if family_t == "metal" and family_o == "metal" and target.material != obj.material:
            bits.append("Hər ikisi metaldır, amma ərintilər fərqlidir")
        else:
            bits.append("Material spektri yaxın düşür")
    elif scores["material"] >= 0.55:
        bits.append("Material qismən oxşardır")
    else:
        bits.append("Material uyğun gəlmir")

    if mode == "material_only":
        bits.append("Yalnız material rejimi: forma və tag nəzərə alınmır")
        return ". ".join(bits)

    if scores["category"] >= 1.0:
        bits.append("kateqoriya/forma üst-üstə düşür")
    elif obj.category == "clutter":
        bits.append("bu evdəki qarışıqlıqdır, axtarılan əşya tipi deyil")

    if scores["visual"] >= 0.75:
        bits.append("vizual iz oxşardır")
    if scores["tag"] >= 1.0:
        bits.append("BLE tag eynidir")
    return "; ".join(bits) + "."


def rank(target: Target, detections: list[PhysicalObject], mode: str = "fusion") -> list[Hit]:
    if mode not in MODES:
        raise ValueError(f"Unknown mode: {mode}")
    weights = MODES[mode]
    hits: list[Hit] = []
    for obj in detections:
        scores = {
            "material": cosine(target.spectrum, obj.spectrum),
            "visual": visual_similarity(target.visual, obj.visual),
            "category": _category_score(target, obj),
            "tag": _tag_score(target, obj),
        }
        confidence = sum(scores[k] * weights[k] for k in weights)
        hits.append(
            Hit(
                obj=obj,
                material_score=scores["material"],
                visual_score=scores["visual"],
                category_score=scores["category"],
                tag_score=scores["tag"],
                confidence=float(confidence),
                explanation=_explain(target, obj, scores, mode),
            )
        )
    hits.sort(key=lambda h: h.confidence, reverse=True)
    return hits
