# Səsli Bilik Yarışı (Telegram + n8n)

Telegram-da həm mətn, həm səs mesajı ilə 10 suallıq viktorina. Bot mövzu və çətinliyi soruşur, cavabları qiymətləndirir, statistikanı saxlayır və hər cavabı **audio mesaj** kimi qaytarır.

## Nə lazımdır

1. İşlək n8n (`docker compose up` — UI: http://localhost:5678)
2. Telegram bot tokeni ([@BotFather](https://t.me/BotFather))
3. OpenAI API açarı (Whisper STT, Chat, TTS)
4. Telegram webhook üçün ictimai URL (lokalda Cloudflare tunnel)

## Workflow-u açmaq

Təzə qurğuda demo import avtomatik götürür:

`n8n/demo-data/workflows/n8nSesliBilikYarisi01.json`

Əgər n8n-də artıq workflow varsa, UI-dən **Import from File** edin.

Sonra hər qırmızı credentials xəbərdarlığında:

| Credential | Harada |
|---|---|
| Telegram Bot | Telegram Trigger, Səs faylını endir, Audio göndər |
| OpenAI | Whisper (STT), OpenAI Chat Model, Səsə çevir (TTS) |

Workflow-u **Active** edin. Telegram webhook n8n-in ictimai ünvanına yazılmalıdır. Windows-da mövcud tunnel:

```bat
start-n8n-tunnel.bat
```

## Oyun axını

```
Telegram (mətn | səs)
        │
        ├─ səs → Get File → Whisper (az) → Set
        └─ mətn → Set
                │
             Merge (append)
                │
     Agent + Memory(session=chat_id) + JSON parser
                │
              Switch
        ┌───────┼────────┬──────────┬────────────┐
   mövzu     sual    statistika  oyun bitdi  sıfırlandı
        │       │         │           │            │
        │       │         │           └────┬───────┘
        │       │         │           Memory Manager
        └───────┴─────────┴───────────────┘
                          │
                     TTS → sendAudio
```

Agent çıxışı sərbəst mətn deyil, JSON-dur:

| `status` | Mənası |
|---|---|
| `ask_topic` | İlk mesaj / mövzu-səviyyə sorğusu (sual yoxdur) |
| `question` | Qiymətləndirmə + növbəti sual |
| `stats` | "neçənci sualdayıq / xalım nədir" — sual dəyişmir |
| `finished` | 10-cu sualdan sonra yekun; yaddaş silinir |
| `reset` | təmizlə / sıfırla / yenidən başla; yaddaş silinir |

Mövzu və ya səviyyə aydın deyilsə default: **ümumi bilik / orta**.

## Test

```bash
cd sesli-bilik
PYTHONPATH=. python3 -m unittest discover -s tests -q
```

Workflow JSON-u yenidən yığmaq:

```bash
python3 sesli-bilik/build_workflow.py
```
