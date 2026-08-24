# Selenium nə vaxt lazımdır?

BeautifulSoup turbo.az **ana səhifəsinin** Premium elanlarını oxuyur,
çünki onlar HTML-də hazır gəlir.

`/autos` tam siyahısı isə JavaScript ilə yüklənir. O səhifə üçün:

```bash
pip install selenium
```

```python
from selenium import webdriver
from selenium.webdriver.common.by import By

browser = webdriver.Chrome()
browser.get("https://example.com")
print(browser.find_element(By.TAG_NAME, "h1").text)
browser.quit()
```

| Vəziyyət | Alət |
| --- | --- |
| Məzmun dərhal görünür | BeautifulSoup |
| "Daha çox" düyməsi / login / scroll | Selenium |
