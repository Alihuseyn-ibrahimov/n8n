"""HTTP API and static UI for TapAI."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import __version__
from .materials import AZ_FAMILY, AZ_MATERIAL, MATERIAL_FAMILIES, PROTOTYPES, get_classifier
from .nlp import CATEGORIES
from .search import search
from .simulator import ROOMS, HomeSimulator

FRONTEND = Path(__file__).resolve().parent.parent / "frontend"
home = HomeSimulator()
get_classifier()

app = FastAPI(
    title="TapAI",
    description="İtən əşyalar üçün hibrid axtarış: material + vizual iz + tag.",
    version=__version__,
)


class SearchBody(BaseModel):
    query: str | None = Field(default=None, examples=["açarımı tap"])
    item_id: str | None = None
    mode: Literal["fusion", "material_only", "visual_only", "tag_only"] = "fusion"
    top_k: int = Field(default=5, ge=1, le=12)


class EnrollBody(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    category: str
    material: str
    room: str
    with_tag: bool = False


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": "tapai", "version": __version__}


@app.get("/api/catalog")
def catalog() -> dict:
    return {
        "materials": [
            {
                "id": key,
                "az": AZ_MATERIAL[key],
                "family": MATERIAL_FAMILIES[key],
                "family_az": AZ_FAMILY[MATERIAL_FAMILIES[key]],
            }
            for key in PROTOTYPES
        ],
        "categories": [
            {
                "id": key,
                "az": meta["az"],
                "default_material": meta["default_material"],
                "shape": meta["shape"],
            }
            for key, meta in CATEGORIES.items()
        ],
        "rooms": [{"id": key, "az": meta["az"], **{k: meta[k] for k in ("x", "y", "w", "h")}} for key, meta in ROOMS.items()],
        "modes": [
            {"id": "fusion", "az": "Fusion (tövsiyə)", "hint": "Material + forma + vizual + tag"},
            {"id": "material_only", "az": "Yalnız material", "hint": "Bütün oxşar metallar işıqlanır"},
            {"id": "visual_only", "az": "Yalnız vizual", "hint": "Rəng və kateqoriya izi"},
            {"id": "tag_only", "az": "Yalnız tag", "hint": "BLE/UWB identifikatoru"},
        ],
    }


@app.get("/api/home")
def get_home() -> dict:
    return {
        "rooms": [{"id": key, **meta} for key, meta in ROOMS.items()],
        "objects": [obj.public_dict() for obj in home.objects.values()],
        "heatmap": home.metal_heatmap(),
    }


@app.get("/api/items")
def list_items() -> dict:
    return {"items": [obj.public_dict() for obj in home.enrolled_items()]}


@app.post("/api/items")
def enroll_item(body: EnrollBody) -> dict:
    if body.category not in CATEGORIES:
        raise HTTPException(400, "Naməlum kateqoriya")
    try:
        obj = home.enroll(
            name=body.name,
            category=body.category,
            material=body.material,
            room=body.room,
            with_tag=body.with_tag,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return obj.public_dict()


@app.post("/api/search")
def run_search(body: SearchBody) -> dict:
    try:
        return search(home, query=body.query, item_id=body.item_id, mode=body.mode, top_k=body.top_k)
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@app.get("/")
def index() -> FileResponse:
    return FileResponse(FRONTEND / "index.html")


app.mount("/static", StaticFiles(directory=FRONTEND), name="static")
