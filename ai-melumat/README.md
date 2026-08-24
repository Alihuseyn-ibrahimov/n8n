# Məlumatçı — AI üçün məlumat çıxarma

Nvidia dərs 5, **Example Script (2)**: web scraping AI-yə xammal yığır.
Modulun UI hissəsi isə həmin xammal üzərində **Human-Agent interfeys nümunələridir**.

Bu qovluq dərsdəki BeautifulSoup / Turbo.az nümunəsini **işlək** edir:

- `turbo_scraping.py` — dərs skripti (fayldan və ya real saytdan)
- `fixtures/turbo_sehife.html` — turbo.az Premium elan qutusunun eyni CSS ünvanları
- brauzer UI — split canvas, grounded cavab, suggestion chips, human-in-the-loop export
- n8n workflow — `[Vaxt] → [oxu] → [tap] → [təmizlə] → [yaz]`

Turbo.az bir çox mühitdə **Cloudflare** arxasındadır. Ona görə dərsin öz ipucu işlədilir:
brauzerdə saxlanmış (və ya bu repo-dakı) HTML-i fayl kimi ver.

## Windows

```powershell
cd $HOME\n8n
git pull origin cursor/ai-melumat-cixarma-eb53
.\start-ai-melumat.bat
```

Brauzer: http://127.0.0.1:8090

CLI (fayldan, şəbəkəsiz):

```powershell
cd ai-melumat
.\.venv\Scripts\python turbo_scraping.py fixtures\turbo_sehife.html
```

## Linux / macOS

```bash
cd ai-melumat
chmod +x start.sh
./start.sh
```

## Ev tapşırığı — qısa cavablar

**Hissə 1**

1. Bloq başlıqları dərhal görünür → **BeautifulSoup**
2. Qəbz şəkli → **OCR**
3. "Daha çox" düyməsi → **Selenium**

**Hissə 2–3** — `python examples/02_homework.py`

**Hissə 4 (nümunə cümlə):** Yığılmış qiymətlərlə AI orta bazar qiymətini çıxarıb istifadəçinin büdcəsinə uyğun elanı tapır.

## n8n

Workflow: `n8n/demo-data/workflows/n8nTurboAzMelumat01.json`

n8n konteyneri `./shared`-i `/data/shared` kimi görür. Fixture ora da kopyalanır:
`shared/turbo_sehife.html`. Import-dan sonra **Execute workflow**.

## Qaydalar

- `robots.txt` oxu, şəxsi məlumat yığma, sorğular arasına fasilə qoy.
- Bu nümunə tədris üçündür; production crawler deyil.
