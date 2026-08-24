from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent


def test_homework_part2_book():
    html = (ROOT / "fixtures" / "kitab.html").read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")
    assert soup.select_one(".title").get_text(strip=True) == "Python ilə AI"
    assert soup.select_one(".price").get_text(strip=True) == "25 AZN"


def test_homework_part3_kia_box():
    html = (ROOT / "fixtures" / "elan_qutusu.html").read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")
    assert soup.select_one(".products-i__name").get_text(strip=True) == "Kia Sorento"
    assert soup.select_one(".products-i__price").get_text(strip=True) == "33 700 ₼"
    assert soup.select_one(".products-i__datetime").get_text(strip=True) == "Bakı, bugün 17:40"
