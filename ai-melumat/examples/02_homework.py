"""Ev tapşırığı — Hissə 2 və 3."""

from bs4 import BeautifulSoup

print("=== Hissə 2 — kitab ===")
html = '<h1 class="title">Python ilə AI</h1><span class="price">25 AZN</span>'
soup = BeautifulSoup(html, "html.parser")
print(soup.select_one(".title").get_text(strip=True))
print(soup.select_one(".price").get_text(strip=True))

print("\n=== Hissə 3 — Turbo.az qutusu ===")
html = """
<div class="products-i">
  <div class="products-i__name">Kia Sorento</div>
  <div class="products-i__price">33 700 ₼</div>
  <div class="products-i__datetime">Bakı, bugün 17:40</div>
</div>"""
soup = BeautifulSoup(html, "html.parser")
print(soup.select_one(".products-i__name").get_text(strip=True))
print(soup.select_one(".products-i__price").get_text(strip=True))
print(soup.select_one(".products-i__datetime").get_text(strip=True))
