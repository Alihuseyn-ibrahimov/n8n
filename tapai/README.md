# TapAI

İtən əşyaları **material + vizual iz + tag** birləşməsi ilə tapan AI prototipi.

Əvvəlcə [PLAN.md](PLAN.md) oxu: niyə tək material radarı kifayət etmir və sistem necə qurulub.

## Windows-da işə salmaq

`tapai` qovluğu ev qovluğunda (`C:\Users\...`) yoxdur. O, bu GitHub repo-nun içindədir. Əvvəlcə kodu götür, sonra Python qur, sonra skripti işə sal.

PowerShell-ə **bütün bloku** yapışdır:

```powershell
cd $HOME
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
  Write-Host "Git yoxdur. https://git-scm.com/download/win"
  return
}
if (-not (Test-Path .\n8n)) {
  git clone https://github.com/Alihuseyn-ibrahimov/n8n.git
}
cd n8n
git fetch origin
git checkout cursor/tapai-lost-item-finder-92f3
git pull origin cursor/tapai-lost-item-finder-92f3
cd tapai
.\start.bat
```

Əgər `start.bat` Python tapmasa:

1. [python.org/downloads](https://www.python.org/downloads/) — Python 3.12 qur
2. Installer-də **Add python.exe to PATH** işarələ
3. PowerShell-i bağla, yenisini aç, `.\start.bat`-ı yenidən işlət

Alternativ:

```powershell
winget install -e --id Python.Python.3.12
```

Brauzerdə: http://127.0.0.1:8088

Repo artıq kompüterindədirsə ev qovluğundan `cd tapai` yazma. Əvəzinə n8n qovluğuna gir:

```powershell
cd \path\to\n8n\tapai
.\start.bat
```

## macOS / Linux

```bash
cd tapai
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8088
```

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
