"""HTML-dən avtomobil elanlarını çıxarmaq (BeautifulSoup).

Dərs 5 / Example Script (2): AI üçün xammal yığmaq.
Selector-lar turbo.az ana səhifəsinin Premium elan qutularına uyğundur.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup

TURBO_AZ_URL = "https://turbo.az/"
DEFAULT_FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "turbo_sehife.html"

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"


def parse_elanlar(html: str, *, base_url: str = "https://turbo.az") -> list[dict[str, str]]:
    """Hər `.products-i` qutusundan ad, qiymət, atribut, yer/vaxt və link çıxarır."""
    soup = BeautifulSoup(html, "html.parser")
    elanlar: list[dict[str, str]] = []

    for element in soup.select(".products-i"):
        ad_el = element.select_one(".products-i__name")
        qiymet_el = element.select_one(".products-i__price")
        atrib_el = element.select_one(".products-i__attributes")
        yer_el = element.select_one(".products-i__datetime")
        link_el = element.select_one(".products-i__link")

        ad = ad_el.get_text(strip=True) if ad_el else ""
        qiymet = qiymet_el.get_text(strip=True) if qiymet_el else ""
        atributlar = atrib_el.get_text(strip=True) if atrib_el else ""
        yer_vaxt = yer_el.get_text(strip=True) if yer_el else ""
        href = link_el.get("href", "") if link_el else ""

        if not ad:
            continue

        if href.startswith("http"):
            link = href
        elif href:
            link = base_url + href
        else:
            link = ""

        seher = yer_vaxt.split(",")[0].strip() if yer_vaxt else ""
        elanlar.append(
            {
                "ad": ad,
                "qiymet": qiymet,
                "atributlar": atributlar,
                "yer_vaxt": yer_vaxt,
                "seher": seher,
                "link": link,
            }
        )

    return elanlar


def qiymet_reqem(qiymet: str) -> int | None:
    """'53 800 ₼' → 53800. Rəqəm yoxdursa None."""
    reqemler = re.sub(r"[^0-9]", "", qiymet or "")
    return int(reqemler) if reqemler else None


def statistika(elanlar: list[dict[str, str]]) -> dict[str, Any]:
    qiymetler = [n for n in (qiymet_reqem(e.get("qiymet", "")) for e in elanlar) if n is not None]
    if not qiymetler:
        return {"say": len(elanlar), "qiymetli_say": 0}

    ortalama = round(sum(qiymetler) / len(qiymetler))
    min_q = min(qiymetler)
    max_q = max(qiymetler)
    ucuz = next(e for e in elanlar if qiymet_reqem(e.get("qiymet", "")) == min_q)
    baha = next(e for e in elanlar if qiymet_reqem(e.get("qiymet", "")) == max_q)
    return {
        "say": len(elanlar),
        "qiymetli_say": len(qiymetler),
        "ortalama": ortalama,
        "en_ucuz": min_q,
        "en_baha": max_q,
        "en_ucuz_ad": ucuz["ad"],
        "en_baha_ad": baha["ad"],
    }


def manat_yaz(n: int) -> str:
    return f"{n:,} ₼".replace(",", " ")


def html_al(source: str | None = None, *, timeout: int = 15) -> tuple[str, str]:
    """HTML qaytarır və mənbəni etiketlənir: file | live | fixture.

    source None olsa əvvəl real saytı sınayır; Cloudflare və ya şəbəkə
    əngəli olanda dərs fixture-una keçir (lesson-dəki fayl rejimi).
    """
    if source:
        path = Path(source)
        return path.read_text(encoding="utf-8"), "file"

    try:
        import requests

        cavab = requests.get(
            TURBO_AZ_URL,
            headers={"User-Agent": USER_AGENT},
            timeout=timeout,
        )
        cavab.raise_for_status()
        text = cavab.text
        if "products-i" in text:
            return text, "live"
    except Exception:
        pass

    if DEFAULT_FIXTURE.exists():
        return DEFAULT_FIXTURE.read_text(encoding="utf-8"), "fixture"
    raise FileNotFoundError("Nə real sayt, nə də fixtures/turbo_sehife.html tapıldı.")


def elanlari_yig(source: str | None = None) -> tuple[list[dict[str, str]], str]:
    html, origin = html_al(source)
    return parse_elanlar(html), origin


def json_yaz(elanlar: list[dict[str, str]], yol: str | Path) -> Path:
    path = Path(yol)
    path.write_text(
        json.dumps(elanlar, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path
