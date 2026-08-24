"""HTTP API + Human-Agent UI (Lesson 5 interface patterns)."""

from __future__ import annotations

import socket
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .agent import SUGGESTIONS, answer
from .scrape import DEFAULT_FIXTURE, elanlari_yig, json_yaz, statistika

ROOT = Path(__file__).resolve().parent.parent
FRONTEND = ROOT / "frontend"
SHARED_JSON = ROOT / "data" / "elanlar.json"
REPO_SHARED = ROOT.parent / "shared" / "elanlar.json"

app = FastAPI(
    title="Məlumatçı",
    description="AI üçün məlumat çıxarma — Human-Agent UI nümunələri.",
    version="1.0.0",
)

_cache: dict = {"elanlar": [], "source": "empty"}


def lan_ip() -> str | None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return None
    finally:
        sock.close()


class ChatBody(BaseModel):
    query: str = Field(min_length=1, max_length=400)


class ScrapeBody(BaseModel):
    source: str | None = Field(
        default="fixture",
        description="fixture | live | və ya HTML fayl yolu",
    )


@app.get("/api/health")
def health() -> dict:
    return {
        "status": "ok",
        "service": "ai-melumat",
        "lan_ip": lan_ip(),
        "source": _cache["source"],
        "say": len(_cache["elanlar"]),
    }


@app.post("/api/scrape")
def scrape(body: ScrapeBody | None = None) -> dict:
    mode = (body.source if body else "fixture") or "fixture"
    if mode == "fixture":
        yol: str | None = str(DEFAULT_FIXTURE)
    elif mode == "live":
        yol = None
    else:
        yol = mode

    try:
        elanlar, origin = elanlari_yig(yol)
    except Exception as err:
        raise HTTPException(status_code=502, detail=str(err)) from err

    _cache["elanlar"] = elanlar
    _cache["source"] = origin
    SHARED_JSON.parent.mkdir(parents=True, exist_ok=True)
    json_yaz(elanlar, SHARED_JSON)
    try:
        REPO_SHARED.parent.mkdir(parents=True, exist_ok=True)
        json_yaz(elanlar, REPO_SHARED)
    except OSError:
        pass

    return {
        "source": origin,
        "elanlar": elanlar,
        "statistika": statistika(elanlar),
        "suggestions": SUGGESTIONS,
    }


@app.get("/api/listings")
def listings() -> dict:
    if not _cache["elanlar"]:
        scrape(ScrapeBody(source="fixture"))
    return {
        "source": _cache["source"],
        "elanlar": _cache["elanlar"],
        "statistika": statistika(_cache["elanlar"]),
        "suggestions": SUGGESTIONS,
    }


@app.post("/api/chat")
def chat(body: ChatBody) -> dict:
    if not _cache["elanlar"]:
        scrape(ScrapeBody(source="fixture"))
    result = answer(body.query, _cache["elanlar"])
    cited = [ _cache["elanlar"][i] for i in result["citations"] if 0 <= i < len(_cache["elanlar"]) ]
    return {
        "text": result["text"],
        "pattern": result["pattern"],
        "citations": result["citations"],
        "elanlar": cited,
        "source": _cache["source"],
    }


@app.get("/")
def index() -> FileResponse:
    return FileResponse(FRONTEND / "index.html")


if FRONTEND.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND), name="static")
