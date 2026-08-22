"""A small apartment the search engine can scan.

Coordinates are percentages of the floor-plan canvas (0–100). Each physical
object has a true material and a noisy sensor reading so the demo behaves like
an imperfect device, not an oracle.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from .materials import AZ_FAMILY, AZ_MATERIAL, MATERIAL_FAMILIES, get_classifier, noisy_signature
from .nlp import CATEGORIES
from .vision import color_from_name, visual_fingerprint

ROOMS = {
    "bedroom": {"az": "Yataq otağı", "x": 0, "y": 0, "w": 50, "h": 42},
    "living": {"az": "Qonaq otağı", "x": 50, "y": 0, "w": 50, "h": 42},
    "hallway": {"az": "Dəhliz", "x": 0, "y": 42, "w": 100, "h": 16},
    "kitchen": {"az": "Mətbəx", "x": 0, "y": 58, "w": 55, "h": 42},
    "balcony": {"az": "Balkon", "x": 55, "y": 58, "w": 45, "h": 42},
}


@dataclass
class PhysicalObject:
    id: str
    name: str
    category: str
    material: str
    room: str
    x: float
    y: float
    color_rgb: tuple[int, int, int]
    tag_id: str | None = None
    enrolled: bool = False
    hidden_note: str = ""
    spectrum: np.ndarray = field(default_factory=lambda: np.zeros(16))
    visual: np.ndarray = field(default_factory=lambda: np.zeros(32))
    photo_fp: np.ndarray | None = None
    has_photo: bool = False

    def public_dict(self) -> dict[str, Any]:
        family = MATERIAL_FAMILIES[self.material]
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "category_az": CATEGORIES.get(self.category, {}).get("az", self.category),
            "material": self.material,
            "material_az": AZ_MATERIAL[self.material],
            "family": family,
            "family_az": AZ_FAMILY[family],
            "room": self.room,
            "room_az": ROOMS[self.room]["az"],
            "x": self.x,
            "y": self.y,
            "color_rgb": list(self.color_rgb),
            "has_tag": bool(self.tag_id),
            "has_photo": self.has_photo,
            "enrolled": self.enrolled,
            "hidden_note": self.hidden_note,
        }


def point_in_room(x: float, y: float, room_id: str) -> bool:
    room = ROOMS[room_id]
    return room["x"] <= x <= room["x"] + room["w"] and room["y"] <= y <= room["y"] + room["h"]


def room_at(x: float, y: float) -> str | None:
    for room_id in ROOMS:
        if point_in_room(x, y, room_id):
            return room_id
    return None


class HomeSimulator:
    def __init__(self, seed: int = 7) -> None:
        self.rng = np.random.default_rng(seed)
        self.objects: dict[str, PhysicalObject] = {}
        self._populate()

    def _make(
        self,
        object_id: str,
        name: str,
        category: str,
        material: str,
        room: str,
        x: float,
        y: float,
        color: tuple[int, int, int] | None = None,
        tag_id: str | None = None,
        enrolled: bool = False,
        hidden_note: str = "",
    ) -> PhysicalObject:
        rgb = color or color_from_name(name)
        obj = PhysicalObject(
            id=object_id,
            name=name,
            category=category,
            material=material,
            room=room,
            x=x,
            y=y,
            color_rgb=rgb,
            tag_id=tag_id,
            enrolled=enrolled,
            hidden_note=hidden_note,
            spectrum=noisy_signature(material, self.rng, noise=0.04),
            visual=visual_fingerprint(rgb, category),
        )
        self.objects[object_id] = obj
        return obj

    def _populate(self) -> None:
        self._make(
            "obj-keys",
            "Açar dəstəsi",
            "keys",
            "brass",
            "living",
            78,
            28,
            color=(196, 148, 58),
            tag_id="tag-keys",
            enrolled=True,
            hidden_note="Divanın yastığının altında",
        )
        self._make(
            "obj-spoon",
            "Polad qaşıq",
            "clutter",
            "steel",
            "kitchen",
            22,
            74,
            color=(170, 176, 182),
            hidden_note="Mətbəx dəzgahında — metal, amma açar deyil",
        )
        self._make(
            "obj-wallet",
            "Dəri cüzdan",
            "wallet",
            "leather",
            "bedroom",
            18,
            22,
            color=(92, 48, 28),
            tag_id="tag-wallet",
            enrolled=True,
            hidden_note="Gödəkçə ciblində",
        )
        self._make(
            "obj-phone",
            "Telefon",
            "phone",
            "glass",
            "hallway",
            48,
            49,
            color=(40, 44, 52),
            enrolled=True,
            hidden_note="Dəhliz konsolunun üstündə",
        )
        self._make(
            "obj-remote",
            "TV pultu",
            "remote",
            "plastic",
            "living",
            62,
            18,
            color=(32, 32, 36),
            enrolled=True,
            hidden_note="Qonaq otağı masaaltı",
        )
        self._make(
            "obj-glasses",
            "Eynək",
            "glasses",
            "plastic",
            "kitchen",
            40,
            68,
            color=(28, 30, 34),
            enrolled=True,
            hidden_note="Mətbəx rəfində",
        )
        self._make(
            "obj-headphones",
            "Qulaqlıq",
            "headphones",
            "plastic",
            "bedroom",
            36,
            12,
            color=(220, 220, 220),
            enrolled=True,
            hidden_note="Tumba üstündə",
        )
        self._make(
            "obj-watch",
            "Qol saatı",
            "watch",
            "steel",
            "kitchen",
            8,
            80,
            color=(192, 196, 200),
            enrolled=True,
            hidden_note="Mətbəx küncündə, yuyulmuş kimi qalıb",
        )
        self._make(
            "obj-pan",
            "Alüminium tava",
            "clutter",
            "aluminum",
            "kitchen",
            12,
            88,
            color=(188, 190, 194),
            hidden_note="Plitənin üstündə — yenə metal",
        )
        self._make(
            "obj-book",
            "Kitab",
            "clutter",
            "paper",
            "living",
            88,
            10,
            color=(180, 60, 50),
            hidden_note="Rəfdə",
        )
        self._make(
            "obj-plant-pot",
            "Keramika dibçək",
            "clutter",
            "ceramic",
            "balcony",
            78,
            78,
            color=(160, 110, 80),
            hidden_note="Balkonda",
        )

    def enrolled_items(self) -> list[PhysicalObject]:
        return [obj for obj in self.objects.values() if obj.enrolled]

    def enroll(
        self,
        name: str,
        category: str,
        material: str,
        room: str,
        x: float | None = None,
        y: float | None = None,
        with_tag: bool = False,
    ) -> PhysicalObject:
        if material not in AZ_MATERIAL:
            raise ValueError(f"Naməlum material: {material}")
        if room not in ROOMS:
            raise ValueError(f"Naməlum otaq: {room}")
        room_meta = ROOMS[room]
        if x is None:
            x = float(room_meta["x"] + room_meta["w"] * 0.5)
        if y is None:
            y = float(room_meta["y"] + room_meta["h"] * 0.5)
        object_id = f"obj-{len(self.objects) + 1}-{name.casefold().replace(' ', '-')[:16]}"
        return self._make(
            object_id,
            name,
            category,
            material,
            room,
            x,
            y,
            tag_id=f"tag-{object_id}" if with_tag else None,
            enrolled=True,
            hidden_note="İstifadəçi qeydiyyatı",
        )

    def scan(self) -> list[PhysicalObject]:
        """Return copies of objects with freshly noised sensor readings."""
        classifier = get_classifier()
        scanned: list[PhysicalObject] = []
        for obj in self.objects.values():
            spectrum = noisy_signature(obj.material, self.rng, noise=0.05)
            guess = classifier.predict(spectrum)
            visual_noise = self.rng.normal(0.0, 0.02, size=obj.visual.shape)
            clone = PhysicalObject(
                id=obj.id,
                name=obj.name,
                category=obj.category,
                material=guess.material if guess.confidence > 0.45 else obj.material,
                room=obj.room,
                x=float(np.clip(obj.x + self.rng.normal(0, 1.2), 0, 100)),
                y=float(np.clip(obj.y + self.rng.normal(0, 1.2), 0, 100)),
                color_rgb=obj.color_rgb,
                tag_id=obj.tag_id,
                enrolled=obj.enrolled,
                hidden_note=obj.hidden_note,
                spectrum=spectrum,
                visual=np.clip(obj.visual + visual_noise, 0.0, 1.0),
            )
            # Keep ground-truth material on the original; clone.material is the
            # classifier's guess so fusion sees realistic sensor error.
            clone.true_material = obj.material  # type: ignore[attr-defined]
            clone.guess_confidence = guess.confidence  # type: ignore[attr-defined]
            clone.guess_family = guess.family  # type: ignore[attr-defined]
            scanned.append(clone)
        return scanned

    def metal_heatmap(self, grid: int = 12) -> list[dict[str, float]]:
        """Inductive-band energy interpolated onto a coarse room grid."""
        cells: list[dict[str, float]] = []
        xs = np.linspace(4, 96, grid)
        ys = np.linspace(4, 96, grid)
        for y in ys:
            for x in xs:
                energy = 0.0
                for obj in self.objects.values():
                    inductive = float(np.mean(obj.spectrum[:4]))
                    dist = ((obj.x - x) ** 2 + (obj.y - y) ** 2) ** 0.5
                    energy += inductive * np.exp(-(dist**2) / (2 * 12.0**2))
                cells.append({"x": float(x), "y": float(y), "energy": float(energy)})
        peak = max(cell["energy"] for cell in cells) or 1.0
        for cell in cells:
            cell["energy"] = cell["energy"] / peak
        return cells
