# TapAI — İtən əşyaları tapmaq üçün AI sistemi

Bu sənəd ideyanın **dürüst texniki qiymətləndirməsi**, tövsiyə olunan arxitektura və addım-addım icra planıdır.

## 1. İdeya nədir?

Evində və ya yaxınlıqda itən əşyanı (açar, cüzdan, telefon, pult…) əvvəlcədən sistemə tanıtmaq, sonra isə **material + forma + siqnal izi** əsasında yerini tapmaq.

Bu düzgün məhsul ideyasıdır. Amma tək başına “material radarı” ilə *məhz sənin açarını* tapmaq fiziki cəhətdən mümkün deyil. Ona görə TapAI **hibrid siqnal birləşməsi** üzərində qurulur.

## 2. Ən vacib həqiqət (bunu əvvəldən qəbul etmək lazımdır)

**Material unikal şəxsiyyət deyil.** Mis açar, polad qaşıq, metal qapı dəstəyi — hamısı “metal”dır. Evdəki sensor yalnız “burada metal var” deyə bilər, “bu sənin açarındır” deyə bilməz.

| Yanaşma | Nə tapır? | Unikal əşya? | Bu gün reallığı |
|---|---|---|---|
| Yalnız material (metal detektor, spektr) | Eyni sinifdəki bütün obyektlər | Xeyr | Laboratoriya / bahalı avadanlıq |
| Yalnız kamera (kompüter görməsi) | Açar *kimi* görünən şeylər | Qismən | Telefonla mümkündür |
| BLE / UWB tag (AirTag tipli) | Məhz o tag-li əşya | Bəli | İstehsalda var |
| **TapAI fusion** | Material filtri + vizual iz + tag + son görünmə | Yaxın | MVP buradadır |

Material **axtarışı daraldan filtr** kimi güclüdür. Unikal ID kimi zəifdir.

Buna görə sistem belə işləyir:

1. Əşyanı qeydiyyatdan keçirirsən: ad, kateqoriya, material, şəkil, istəsən tag.
2. Axtarış zamanı ev “skan” olunur.
3. Hər namizəd 4 siqnal üzrə qiymətləndirilir: material, vizual oxşarlıq, kateqoriya/forma, tag.
4. Nəticələr birləşdirilib (fusion) sıralanır.

Yalnız material rejimində qaşıq da, açar da metal kimi görünür — UI bunu açıq göstərir. Fusion rejimində açar qalib gəlir.

## 3. Niyə “təmiz material radarı” istehlak məhsulu ola bilməz?

- **Spektral eyniləşdirmə** (NIR, hyperspectral, THz) işıq, boya, kisə, cib və digər əşyaların kölgəsindən asılıdır.
- **Rentgen / güclü RF** təhlükəsizlik və lisenziya problemi yaradır.
- Evdə eyni materialdan onlarla obyekt var.
- Kiçik əşya (açar) divar arxasında, paltarda, divanın altında spektral cəhətdən “itir”.

Material sensorunu **tamamilə atmaq** da səhvdir. Metal detektor, tutum sensoru və vizual material təsnifatı axtarışı sürətləndirir: “metal axtarıram” → plastik pultlar kənara.

## 4. Tövsiyə olunan məhsul: 3 qatlı TapAI

```
┌─────────────────────────────────────────────────────────┐
│  Tətbiq: “Açarımı tap” / əşya siyahısı / xəritə         │
├─────────────────────────────────────────────────────────┤
│  AI mühərriki                                           │
│  • sorğu anlayışı (Azərbaycan dili)                     │
│  • material təsnifatı                                   │
│  • vizual barmaq izi                                    │
│  • fusion sıralama                                      │
├───────────────┬─────────────────┬───────────────────────┤
│ Telefon kamerası │ BLE/UWB tag │ Ev anker / sensor     │
│ (görüntü)        │ (unikal ID) │ (material + məsafə)   │
└───────────────┴─────────────────┴───────────────────────┘
```

### Qat A — Proqram (indiki addım)

Ev simulyatoru, əşya qeydiyyatı, material AI, fusion axtarış, veb interfeys.

### Qat B — Telefon

Kameradan obyekt aşkarlama + material təxmin + “son görüldüyü yer”.

### Qat C — Cihaz

Kiçik tag əşyaya yapışır (unikal ID). Evdə 2–3 anker otaq-səviyyəli yer verir. Material sensoru namizədləri filtr edir.

## 5. AI mühəndisliyi: nəyi öyrədirik?

| Model | Giriş | Çıxış | İndi |
|---|---|---|---|
| Material klassifikatoru | 16 kanallı simulyasiya spektri (induktiv + dielektrik + NIR + mmWave) | `brass`, `steel`, `leather`… | Prototipə ən yaxın spektr (cosine) |
| Vizual iz | şəkil və ya rəng/tekstur vektoru | oxşarlıq skoru | Histogram + kateqoriya |
| Sorğu NLP | “açarımı tap”, “cüzdan haradadır” | əşya / kateqoriya | Qayda + lüğət |
| Fusion | 4 skoru | yekun inam + izah | Çəki cəmi |

Gələcəkdə CLIP/YOLO əsl şəkillər üçün əlavə olunur. İndi ağır GPU modeli yoxdur: məntiqi və test oluna bilən mühərrik var.

## 6. Addım-addım yol xəritəsi

### Addım 0 — Plan və fizika sərhədi

Bu sənəd. Materialın filtr olduğu qəbul edilir.

### Addım 1 — Proqram MVP (bu PR)

- Əşya qeydiyyatı (ad, material, kateqoriya, rəng izi)
- Simulyasiya olunmuş ev (otaqlar + gizlənmiş əşyalar)
- Material skanı (heatmap)
- Fusion axtarış
- Azərbaycan dilində sorğu
- “Yalnız material” vs “Fusion” müqayisəsi
- API + veb UI + testlər

### Addım 2 — Real kamera

- Telefonda obyekt deteksiyası (açar, cüzdan, telefon)
- Materialı görüntüdən təxmin etmək
- “Son görüldüyü yer” tarixçəsi

### Addım 3 — Tag prototipi

- BLE beacon və ya hazır modul (nRF, ESP32)
- RSSI ilə otaq təxmini
- UWB (DW3000) ilə 10–30 sm dəqiqlik — *əsl “haradadır”*

### Addım 4 — Ev ankerləri

- 2–3 stasionar qəbuledici
- Otaq xəritəsi
- n8n ilə bildiriş: “Açar qonaq otağındadır”

### Addım 5 — Eksperimental material sensoru (tədqiqat)

- Kiçik induktiv metal loop
- Tutum sensoru (plastik/dəri fərqi)
- Ucuz NIR LED-lər
- Məqsəd: unikal ID yox, **namizəd filtrini** yaxşılaşdırmaq

## 7. Niyə bu arxitektura düzgündür?

1. **Bu gün işləyən məhsul** (tag + kamera) ilə **sənin orijinal ideyanı** (material) birləşdirir.
2. Elmi cəhətdən yalan vəd vermir.
3. Hər addım ayrıca dəyər verir: yalnız proqram da demo kimi işləyir.
4. Test edilə bilir: fusion açarı qaşıqdan ayırmalıdır; material-only isə hər ikisini metal kimi göstərməlidir.

## 8. MVP-də nə var?

```
tapai/
  PLAN.md           ← bu sənəd
  README.md         ← işə salma
  app/              ← FastAPI + AI mühərriki
  frontend/         ← ev xəritəsi və axtarış UI
  tests/            ← fizika + fusion + API testləri
```

İşə salma: `tapai/README.md`.

## 9. Növbəti qərarlar (sonra)

- Real YOLO/CLIP əlavə etmək
- ESP32 BLE tag prototipi
- n8n workflow: tapıldı → Telegram/SMS
- Məxfilik: hər şey lokal, bulud məcburi deyil
