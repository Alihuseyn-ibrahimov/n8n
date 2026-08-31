"""HTTP API and static UI for TapAI."""

from __future__ import annotations

import socket
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import __version__
from .camera import enroll_photo, load_sightings, photos_dir, search_photo
from .materials import AZ_FAMILY, AZ_MATERIAL, MATERIAL_FAMILIES, PROTOTYPES, get_classifier
from .nlp import CATEGORIES
from .search import search
from .simulator import ROOMS, HomeSimulator

FRONTEND = Path(__file__).resolve().parent.parent / "frontend"
home = HomeSimulator()
get_classifier()


def lan_ip() -> str | None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return None
    finally:
        sock.close()

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
    return {
        "status": "ok",
        "service": "tapai",
        "version": __version__,
        "lan_ip": lan_ip(),
        "camera": True,
    }


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


@app.post("/api/items/{item_id}/photo")
async def attach_photo(item_id: str, photo: UploadFile = File(...)) -> dict:
    data = await photo.read()
    if len(data) < 32:
        raise HTTPException(400, "Şəkil boşdur")
    try:
        item = enroll_photo(home, item_id, data)
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from exc
    except Exception as exc:  # noqa: BLE001 — invalid image bytes
        raise HTTPException(400, f"Şəkil oxunmadı: {exc}") from exc
    return item.public_dict()


@app.get("/api/items/{item_id}/photo")
def get_photo(item_id: str) -> Response:
    path = photos_dir() / f"{item_id}.jpg"
    if not path.exists():
        raise HTTPException(404, "Referans foto yoxdur")
    return FileResponse(path, media_type="image/jpeg")


@app.post("/api/camera/search")
async def camera_search(
    photo: UploadFile = File(...),
    item_id: str | None = Form(default=None),
    lat: float | None = Form(default=None),
    lon: float | None = Form(default=None),
) -> dict:
    data = await photo.read()
    if len(data) < 32:
        raise HTTPException(400, "Şəkil boşdur")
    empty_id = item_id.strip() if item_id else None
    if empty_id == "":
        empty_id = None
    try:
        return search_photo(home, data, item_id=empty_id, lat=lat, lon=lon)
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(400, f"Şəkil oxunmadı: {exc}") from exc


@app.get("/api/camera/last-seen")
def last_seen() -> dict:
    return {"last_seen": load_sightings()[:20]}


@app.get("/")
def index() -> FileResponse:
    return FileResponse(FRONTEND / "index.html")


app.mount("/static", StaticFiles(directory=FRONTEND), name="static")
