"""Azerbaijani query understanding for the MVP.

A later step can swap this for an LLM. Rules are enough for a demo and they
are testable without a GPU.
"""

from __future__ import annotations

from dataclasses import dataclass

CATEGORIES = {
    "keys": {
        "az": "açar",
        "aliases": ["açar", "açarlar", "açarımı", "açarım", "klüç", "key"],
        "default_material": "brass",
        "shape": "kiçik metal, dişli",
    },
    "wallet": {
        "az": "cüzdan",
        "aliases": ["cüzdan", "cüzdanı", "cüzdanım", "cüzdanımı", "pulqabı", "wallet"],
        "default_material": "leather",
        "shape": "düzbucaqlı, yastı",
    },
    "phone": {
        "az": "telefon",
        "aliases": ["telefon", "telefonu", "telefonum", "mobil", "phone"],
        "default_material": "glass",
        "shape": "düzbucaqlı şüşə+metal",
    },
    "remote": {
        "az": "pult",
        "aliases": ["pult", "pultu", "pultum", "remote"],
        "default_material": "plastic",
        "shape": "uzunsov plastik",
    },
    "glasses": {
        "az": "eynək",
        "aliases": ["eynək", "eynəyi", "eynəyim", "glasses"],
        "default_material": "plastic",
        "shape": "çərçivə + linza",
    },
    "headphones": {
        "az": "qulaqlıq",
        "aliases": ["qulaqlıq", "qulaqlığı", "airpods", "headphones"],
        "default_material": "plastic",
        "shape": "kiçik plastik+metal",
    },
    "watch": {
        "az": "saat",
        "aliases": ["saat", "saatı", "saatım", "watch"],
        "default_material": "steel",
        "shape": "dairəvi metal",
    },
    "card": {
        "az": "kart",
        "aliases": ["kart", "kartı", "kartım", "bank kartı"],
        "default_material": "plastic",
        "shape": "nazik plastik",
    },
}


@dataclass
class ParsedQuery:
    raw: str
    category: str | None
    item_hint: str | None
    wants_find: bool


def parse_query(text: str) -> ParsedQuery:
    raw = (text or "").strip()
    lowered = raw.casefold()
    category = None
    hint = None
    for cat, meta in CATEGORIES.items():
        for alias in meta["aliases"]:
            if alias.casefold() in lowered:
                category = cat
                hint = alias
                break
        if category:
            break
    find_words = ("tap", "harada", "axtar", "find", "where")
    wants_find = any(word in lowered for word in find_words) or bool(category)
    return ParsedQuery(raw=raw, category=category, item_hint=hint, wants_find=wants_find)
