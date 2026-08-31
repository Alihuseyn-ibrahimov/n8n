# Instagram DM piloru — ManyChat + MasterNR1

Meta-nın `instagram_manage_messages` Advanced Access-i (App Review) olmadan
real Instagram hesablarından gələn DM-lər Business API-yə **düşmür**. Bu,
2026-07-29-da DVX-də təsdiqlənib. Ona görə canlı pilor **ManyChat relay**-dir:
ManyChat Instagram-ı öz Advanced Access-i ilə oxuyur, mətni bizə POST edir,
cavabı özü göndərir.

Görüşdə göstəriləcək canlı səhifə: **Al Balı** (`@al.bali.az`) — admin sənindir,
qiymət/FAQ realdır, sifariş kanalı yalnız DM-dir. Master NR 1 üçün eyni axın
işləyir: yalnız `Business` + KB dəyişir.

## 0. Nə lazımdır (səndən)

| Nə | Qeyd |
|---|---|
| Instagram Professional + bağlı Facebook Page | Al Balı üçün artıq var |
| ManyChat hesabı (Free kifayətdir) | manychat.com |
| `GROQ_API_KEY` | console.groq.com — görüşdən əvvəl kvotaya bax |
| cloudflared | n8n tuneli ilə eyni proqram |

## 1. Lokal server + seed

PyCharm terminalində (`masternr1` qovluğu):

```bat
.venv\Scripts\python manage.py migrate
.venv\Scripts\python manage.py seed_albali
.venv\Scripts\python manage.py runserver 8055
```

`seed_albali` çap etdiyi `manychat_token`-i kopyala (ManyChat-ə lazımdır).
Operator: `albali` / `demopass123` — panel: http://127.0.0.1:8055/inbox/

Master NR 1 brendi ilə eyni relay:

```bat
.venv\Scripts\python manage.py seed_masternr1
.venv\Scripts\python manage.py enable_instagram_relay --slug=master-nr-1
```

## 2. HTTPS tunnel (Meta/ManyChat localhost qəbul etmir)

İkinci terminal:

```bat
"C:\Program Files (x86)\cloudflared\cloudflared.exe" tunnel --url http://localhost:8055
```

Çıxışdakı `https://xxxx.trycloudflare.com` ünvanını götür.
DEBUG rejimində boş `DJANGO_ALLOWED_HOSTS` artıq `*`-dır — hostname dəyişəndə
.env yeniləməyə ehtiyac yoxdur.

Lokal yoxlama (tokeni əvəz et):

```bat
curl -s -X POST http://127.0.0.1:8055/webhook/manychat/ -H "Content-Type: application/json" -H "X-Relay-Token: TOKEN" -d "{\"subscriber_id\":\"test-1\",\"text\":\"qiymet nedir?\"}"
```

JSON-da `reply` sahəsi dolu olmalıdır. Inbox-da söhbət görünməlidir.

## 3. ManyChat — Instagram səhifəsini bağla

1. [manychat.com](https://manychat.com) → Sign up / Log in (Facebook ilə).
2. **Settings → Channels → Instagram** → **Connect Instagram**.
3. Al Balı-nın bağlı olduğu Facebook Page-i seç, icazələri təsdiqlə.
4. Status **Connected** olmalıdır. Instagram-da səhifəyə test DM yazanda
   ManyChat → Audience-də subscriber görünür.

## 4. ManyChat avtomatlaşdırması (Default Reply)

**Automation → Rules** (və ya **Instagram → Default Reply**):

Trigger: Instagram-da yeni mətn mesajı.

Addımlar:

1. **External Request**
   - Method: `POST`
   - URL: `https://xxxx.trycloudflare.com/webhook/manychat/`
   - Headers:
     - `Content-Type` = `application/json`
     - `X-Relay-Token` = `seed_albali`-nin çap etdiyi token
   - Body (JSON):

```json
{
  "subscriber_id": "{{user_id}}",
  "text": "{{last_input_text}}",
  "first_name": "{{first_name}}",
  "last_name": "{{last_name}}"
}
```

   - Response mapping: `reply` → Custom Field `bot_reply`
     (ManyChat-də əvvəl Custom Field yarat: `bot_reply`, type Text)

2. **Send Message** → `{{bot_reply}}`

   *Alternativ:* External Request-i **Dynamic Content** kimi işlət — cavab
   artıq ManyChat v2 formatındadır (`content.messages`). Bu halda 2-ci addım
   lazım deyil.

3. Publish / Activate.

**Vacib:** eyni mesajı həm Default Reply, həm də başqa Live Chat operatoru
cavablamasın. Pilot zamanı ManyChat Inbox-da auto-reply aktiv qalsın.

## 5. Canlı sınaq (görüşdən əvvəl)

1. Öz şəxsi Instagram-ından `@al.bali.az`-a yaz: `salam`
2. Bot qiymət/çarə haqqında qısa cavab verməlidir (KB-dən).
3. `qiymət` yaz → süzmə/şanı cədvəli.
4. `1 kq süzmə, adım Aysel, telefon 0501234567, 28 May metrosu` →
   qeydiyyat + (Telegram qoşulubsa) qrup bildirişi.
5. http://127.0.0.1:8055/inbox/ — söhbət və `CustomerRequest` görünməlidir.

Uğursuzdursa **mesaj mətninə güvənmə**. Yoxla:

- Django konsolu: 200 vs 403 (yanlış token) vs DisallowedHost
- ManyChat Request log (External Request status)
- DB: `Message` yazıları
- Groq: `rate_limit_exceeded` / `tool_use_failed`

## 6. Görüşdə nə göstərirsən (10 dəq)

1. Telefonda canlı: şəxsi IG → Al Balı DM → bot cavabı.
2. Laptopda `/inbox/` eyni söhbət.
3. Admin-də Al Balı KB (qiymət cədvəli).
4. Cümlə: *Master NR 1 üçün kod dəyişmir. Sizin Instagram Page + öz
   proqram/qiymət cədvəliniz. ManyChat-də səhifəni dəyişmək 15 dəqiqədir.*

## 7. Tunel düşəndə

cloudflared quick tunnel URL-i hər restartda dəyişir. Yeni URL-i ManyChat
External Request-ə yapışdır. Daimi ünvan üçün Faza 5 (`bot.prdostu.com`).
