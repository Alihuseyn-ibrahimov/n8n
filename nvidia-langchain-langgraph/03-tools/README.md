# Example Code (3) — Ev tapşırığı

İki tool: `vergi_hesabla` və `endirim_tətbiq_et`. Hər ikisi `hesab_toolkit` siyahısındadır.

## Lokal sayt

```bash
pip install -r requirements.txt
python3 -m uvicorn web.app:app --app-dir nvidia-langchain-langgraph/03-tools --host 0.0.0.0 --port 8080
```

Aç: http://localhost:8080

Konsol üçün:

```bash
python3 ev_tapshirigi.py
```
