from app.agent import answer
from app.scrape import parse_elanlar
from pathlib import Path

ELANLAR = parse_elanlar(
    (Path(__file__).resolve().parent.parent / "fixtures" / "turbo_sehife.html").read_text(
        encoding="utf-8"
    )
)


def test_budget_filters_and_cites():
    result = answer("50 minə nə var?", ELANLAR)
    assert result["citations"]
    cited = [ELANLAR[i]["ad"] for i in result["citations"]]
    assert "Lada Vesta" in cited
    assert "Chevrolet Malibu" in cited
    assert "Toyota Land Cruiser" not in cited
    assert "50 000" in result["text"] or "50000" in result["text"].replace(" ", "")


def test_cheapest():
    result = answer("Ən ucuz hansıdır?", ELANLAR)
    assert "Lada Vesta" in result["text"]


def test_baku_toyota():
    result = answer("Bakıda Toyota varmı?", ELANLAR)
    assert result["citations"]
    names = [ELANLAR[i]["ad"] for i in result["citations"]]
    assert any("Toyota" in n for n in names)
    assert all(ELANLAR[i]["seher"] == "Bakı" for i in result["citations"])
