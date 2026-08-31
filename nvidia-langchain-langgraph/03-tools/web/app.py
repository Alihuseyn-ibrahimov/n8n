"""Hesab Toolkit — tapşırığın lokal veb təqdimatı."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ev_tapshirigi import endirim_tətbiq_et, hesab_toolkit, vergi_hesabla  # noqa: E402

STATIC = Path(__file__).resolve().parent / "static"

app = FastAPI(title="Hesab Toolkit")
app.mount("/static", StaticFiles(directory=STATIC), name="static")


class VergiSorgu(BaseModel):
    mebleg: float = Field(ge=0)
    faiz: float


class EndirimSorgu(BaseModel):
    qiymet: float = Field(ge=0)
    faiz: float


@app.get("/")
def ana_sehife() -> FileResponse:
    return FileResponse(STATIC / "index.html")


@app.get("/api/toolkit")
def toolkit() -> dict:
    return {
        "tools": [
            {"ad": t.name, "tesvir": t.description.strip()}
            for t in hesab_toolkit
        ]
    }


@app.post("/api/vergi")
def vergi(sorgu: VergiSorgu) -> dict:
    cagiris = {"məbləğ": sorgu.mebleg, "faiz": sorgu.faiz}
    netice = vergi_hesabla.invoke(cagiris)
    invoke = f'{vergi_hesabla.name}.invoke({json.dumps(cagiris, ensure_ascii=False)})'
    return {
        "tool": vergi_hesabla.name,
        "invoke": invoke,
        "netice": netice,
        "xeta": False,
    }


@app.post("/api/endirim")
def endirim(sorgu: EndirimSorgu) -> dict:
    cagiris = {"qiymət": sorgu.qiymet, "faiz": sorgu.faiz}
    netice = endirim_tətbiq_et.invoke(cagiris)
    xeta = isinstance(netice, str)
    invoke = f'{endirim_tətbiq_et.name}.invoke({json.dumps(cagiris, ensure_ascii=False)})'
    return {
        "tool": endirim_tətbiq_et.name,
        "invoke": invoke,
        "netice": netice,
        "xeta": xeta,
    }


@app.get("/api/demo")
def demo() -> dict:
    vergi = vergi_hesabla.invoke({"məbləğ": 200, "faiz": 18})
    endirim_ok = endirim_tətbiq_et.invoke({"qiymət": 100, "faiz": 20})
    endirim_xeta = endirim_tətbiq_et.invoke({"qiymət": 100, "faiz": 150})
    adlar = [t.name for t in hesab_toolkit]
    return {
        "vergi": vergi,
        "endirim": endirim_ok,
        "endirim_xeta": endirim_xeta,
        "adlar": adlar,
    }
