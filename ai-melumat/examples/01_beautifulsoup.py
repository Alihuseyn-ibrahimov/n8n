"""Dərs nümunəsi: hazır HTML-dən ad və qiymət."""

from bs4 import BeautifulSoup

html = "<h1>iPhone 15</h1><span class=\"price\">1999 AZN</span>"
soup = BeautifulSoup(html, "html.parser")

ad = soup.select_one("h1").get_text()
qiymet = soup.select_one(".price").get_text()

print(ad)
print(qiymet)
