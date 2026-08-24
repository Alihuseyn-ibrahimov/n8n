# ============================================
#  TURBO.AZ SCRAPING — DƏRS NÜMUNƏSİ (Python)
#  İşə salmaq:  python3 turbo_scraping.py
# ============================================
#
#  İki rejim:
#  1) REAL SAYT:   python3 turbo_scraping.py
#  2) FAYLDAN:     python3 turbo_scraping.py fixtures/turbo_sehife.html
#
#  Lazımi kitabxanalar:
#     pip install requests beautifulsoup4
#
#  Qeyd: bəzi mühitlərdə turbo.az birbaşa açılmaya bilər
#  (Cloudflare / şəbəkə). O halda script avtomatik
#  fixtures/turbo_sehife.html-ə keçir.
# ============================================

from __future__ import annotations

import sys
from pathlib import Path

# `python turbo_scraping.py` üçün qovluğu path-ə əlavə et
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.scrape import elanlari_yig, json_yaz, manat_yaz, statistika  # noqa: E402


def main() -> None:
    fayl = sys.argv[1] if len(sys.argv) > 1 else None
    if fayl:
        print(f"Fayldan oxunur: {fayl}\n")
    else:
        print("Real saytdan çəkilir: https://turbo.az/\n")

    elanlar, origin = elanlari_yig(fayl)
    if origin == "fixture":
        print("Qeyd: real sayt açılmadı, dərs fixture-u istifadə olunur.\n")

    print(f"=== {len(elanlar)} elan tapıldı ===\n")

    for i, e in enumerate(elanlar[:10], start=1):
        print(f"{i}. {e['ad']}")
        print(f"   Qiymət:    {e['qiymet']}")
        print(f"   Məlumat:   {e['atributlar']}")
        print(f"   Yer/Vaxt:  {e['yer_vaxt']}")
        print(f"   Link:      {e['link']}\n")

    out = Path(__file__).resolve().parent / "elanlar.json"
    json_yaz(elanlar, out)
    print(f'Bütün məlumat "{out.name}" faylına yazıldı.\n')

    stats = statistika(elanlar)
    if stats.get("qiymetli_say"):
        print("=== Sadə statistika ===")
        print(f"Orta qiymət: {manat_yaz(stats['ortalama'])}")
        print(f"Ən ucuz:     {manat_yaz(stats['en_ucuz'])}")
        print(f"Ən baha:     {manat_yaz(stats['en_baha'])}")


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        print("Xəta baş verdi:", err)
        print("\nİpucu: real sayt açılmırsa, HTML faylını belə ver:")
        print("   python3 turbo_scraping.py fixtures/turbo_sehife.html")
        raise SystemExit(1)
