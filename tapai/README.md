# TapAI

İtən əşyaları **material + vizual iz + tag** birləşməsi ilə tapan AI prototipi.

Əvvəlcə [PLAN.md](PLAN.md) oxu: niyə tək material radarı kifayət etmir və sistem necə qurulub.

## İşə salmaq

```bash
cd tapai
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8088
```

Sonra brauzerdə: http://127.0.0.1:8088

## Nə yoxlanır?

```bash
cd tapai
python3 -m pytest -q
```

Vacib test: fusion rejimində açar qaşıqdan üstündür; yalnız-material rejimində hər ikisi metal kimi yüksək skor alır.

## API

| Metod | Yol | Məqsəd |
|---|---|---|
| GET | `/api/health` | sağlamlıq |
| GET | `/api/catalog` | materiallar, otaqlar, rejimlər |
| GET | `/api/home` | ev xəritəsi + heatmap |
| GET | `/api/items` | qeydiyyatlı əşyalar |
| POST | `/api/items` | yeni əşya tanımaq |
| POST | `/api/search` | `{"query":"açarımı tap","mode":"fusion"}` |

## Bu addımda nə yoxdur?

Real kamera, real BLE tag və fiziki spektral sensor. Ev **simulyasiyadır** — mühərrikin məntiqi isə realdır və növbəti addımda eyni API-yə sensorlar qoşulur.
