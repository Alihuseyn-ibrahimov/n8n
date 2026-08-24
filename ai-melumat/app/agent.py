"""Grounded agent: elan JSON-una əsasən Azərbaycan dilində cavab.

LLM tələb etmir — Human-Agent UI nümunəsi üçün siyahıdan sitat gətirir.
"""

from __future__ import annotations

import re
from typing import Any

from .scrape import manat_yaz, qiymet_reqem, statistika

SUGGESTIONS = [
    "Orta qiymət nədir?",
    "50 minə nə var?",
    "Ən ucuz hansıdır?",
    "Bakıda Toyota varmı?",
    "Yeni, 0 km maşınlar",
]


def _norm(text: str) -> str:
    return (text or "").casefold()


def _budget(query: str) -> int | None:
    # "50 min", "50000", "50 000", "40 minə"
    q = _norm(query).replace("ə", "e")
    m = re.search(r"(\d[\d\s]*)\s*min", q)
    if m:
        n = int(re.sub(r"\D", "", m.group(1)))
        return n * 1000 if n < 1000 else n
    m = re.search(r"(\d[\d\s]{2,})", q)
    if m:
        n = int(re.sub(r"\D", "", m.group(1)))
        if n >= 1000:
            return n
    return None


def _seherler(elanlar: list[dict[str, str]]) -> list[str]:
    seen: list[str] = []
    for e in elanlar:
        s = e.get("seher") or ""
        if s and s not in seen:
            seen.append(s)
    return seen


def _markalar(elanlar: list[dict[str, str]]) -> list[str]:
    seen: list[str] = []
    for e in elanlar:
        first = (e.get("ad") or "").split()[0] if e.get("ad") else ""
        if first and first not in seen:
            seen.append(first)
    return seen


def _cite(elanlar: list[dict[str, str]], matches: list[dict[str, str]]) -> list[int]:
    ids: list[int] = []
    for m in matches:
        try:
            ids.append(elanlar.index(m))
        except ValueError:
            continue
    return ids


def answer(query: str, elanlar: list[dict[str, str]]) -> dict[str, Any]:
    q = _norm(query)
    stats = statistika(elanlar)

    if not elanlar:
        return {
            "text": "Hələ elan yoxdur. Soldan «Elanları yığ» düyməsinə bas.",
            "citations": [],
            "pattern": "empty-state",
        }

    if any(k in q for k in ("orta", "ortalama", "statistika", "statistika")):
        text = (
            f"{stats['say']} elanın orta qiyməti {manat_yaz(stats['ortalama'])}. "
            f"Ən ucuz: {stats['en_ucuz_ad']} ({manat_yaz(stats['en_ucuz'])}). "
            f"Ən baha: {stats['en_baha_ad']} ({manat_yaz(stats['en_baha'])})."
        )
        return {"text": text, "citations": [], "pattern": "grounded-summary"}

    if any(k in q for k in ("ucuz", "ucuzu", "ən ucuz", "en ucuz")):
        n = stats.get("en_ucuz")
        hits = [e for e in elanlar if qiymet_reqem(e.get("qiymet", "")) == n]
        hit = hits[0]
        text = (
            f"Ən ucuz elan **{hit['ad']}** — {hit['qiymet']}. "
            f"{hit['atributlar']}. Yer: {hit['yer_vaxt']}."
        )
        return {"text": text, "citations": _cite(elanlar, hits), "pattern": "citation-card"}

    if any(k in q for k in ("baha", "bahalı", "ən baha", "en baha")):
        n = stats.get("en_baha")
        hits = [e for e in elanlar if qiymet_reqem(e.get("qiymet", "")) == n]
        hit = hits[0]
        text = (
            f"Ən bahalı elan **{hit['ad']}** — {hit['qiymet']}. "
            f"{hit['atributlar']}. Yer: {hit['yer_vaxt']}."
        )
        return {"text": text, "citations": _cite(elanlar, hits), "pattern": "citation-card"}

    budget = _budget(query)
    if budget:
        hits = [
            e
            for e in elanlar
            if (qiymet_reqem(e.get("qiymet", "")) or 10**12) <= budget
        ]
        if not hits:
            text = f"{manat_yaz(budget)} büdcəyə düşən elan tapılmadı. Orta bazar {manat_yaz(stats['ortalama'])} ətrafındadır."
            return {"text": text, "citations": [], "pattern": "grounded-summary"}
        lines = [f"{i+1}. {e['ad']} — {e['qiymet']} ({e['seher']})" for i, e in enumerate(hits)]
        text = (
            f"{manat_yaz(budget)} büdcəyə **{len(hits)}** elan düşür:\n"
            + "\n".join(lines)
        )
        return {"text": text, "citations": _cite(elanlar, hits), "pattern": "citation-card"}

    if any(k in q for k in ("0 km", "0km", "yeni", "sıfır", "sifir")):
        hits = [e for e in elanlar if "0 km" in (e.get("atributlar") or "").lower()]
        if not hits:
            return {
                "text": "0 km elan bu siyahıda yoxdur.",
                "citations": [],
                "pattern": "empty-state",
            }
        names = ", ".join(f"{e['ad']} ({e['qiymet']})" for e in hits)
        return {
            "text": f"Yeni (0 km) elanlar: {names}.",
            "citations": _cite(elanlar, hits),
            "pattern": "citation-card",
        }

    seher_hit = next((s for s in _seherler(elanlar) if _norm(s) in q), None)
    marka_hit = next((m for m in _markalar(elanlar) if _norm(m) in q), None)

    filtered = list(elanlar)
    notes: list[str] = []
    if seher_hit:
        filtered = [e for e in filtered if e.get("seher") == seher_hit]
        notes.append(seher_hit)
    if marka_hit:
        filtered = [e for e in filtered if _norm(e.get("ad", "")).startswith(_norm(marka_hit))]
        notes.append(marka_hit)

    if seher_hit or marka_hit:
        if not filtered:
            text = f"{' / '.join(notes)} üçün elan tapılmadı."
            return {"text": text, "citations": [], "pattern": "empty-state"}
        lines = [f"{e['ad']} — {e['qiymet']} ({e['yer_vaxt']})" for e in filtered]
        text = f"{' + '.join(notes)}: **{len(filtered)}** elan.\n" + "\n".join(lines)
        return {
            "text": text,
            "citations": _cite(elanlar, filtered),
            "pattern": "citation-card",
        }

    preview = ", ".join(f"{e['ad']} ({e['qiymet']})" for e in elanlar[:4])
    text = (
        f"Bu siyahıda {stats['say']} elan var, orta qiymət {manat_yaz(stats['ortalama'])}. "
        f"Məsələn: {preview}. Büdcə, marka və ya şəhər yaz — uyğun elanları göstərim."
    )
    return {"text": text, "citations": list(range(min(4, len(elanlar)))), "pattern": "suggestion-followup"}
