from pathlib import Path

from app.scrape import manat_yaz, parse_elanlar, qiymet_reqem, statistika

FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "turbo_sehife.html"


def test_parse_skips_banner_and_keeps_twelve():
    html = FIXTURE.read_text(encoding="utf-8")
    elanlar = parse_elanlar(html)
    assert len(elanlar) == 12
    assert all(e["ad"] for e in elanlar)
    camry = next(e for e in elanlar if e["ad"] == "Toyota Camry")
    assert camry["qiymet"] == "53 800 ₼"
    assert camry["atributlar"] == "2025, 2.0 L, 53 900 km"
    assert camry["seher"] == "Şəmkir"
    assert camry["link"].endswith("/autos/10499280-toyota-camry")


def test_statistika_matches_lesson_range():
    elanlar = parse_elanlar(FIXTURE.read_text(encoding="utf-8"))
    stats = statistika(elanlar)
    assert stats["en_ucuz"] == 24800
    assert stats["en_baha"] == 144500
    assert stats["en_ucuz_ad"] == "Lada Vesta"
    assert stats["en_baha_ad"] == "Toyota Land Cruiser"
    assert 30000 < stats["ortalama"] < 90000
    assert manat_yaz(24800) == "24 800 ₼"


def test_qiymet_parser():
    assert qiymet_reqem("53 800 ₼") == 53800
    assert qiymet_reqem("Reklam") is None
