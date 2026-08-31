"""Lightweight visual fingerprints.

A production system would use CLIP or a dedicated object detector. This MVP
keeps a deterministic 32-d vector so tests stay fast and offline:

* 24 bins: RGB histogram proxy (8 per channel, from a declared color)
* 8 bins: category one-hot (padded)
"""

from __future__ import annotations

import hashlib

import numpy as np

from .nlp import CATEGORIES

CHANNELS = 8
CATEGORY_DIM = 8
VISUAL_DIM = CHANNELS * 3 + CATEGORY_DIM


def _channel_hist(value: int) -> np.ndarray:
    hist = np.zeros(CHANNELS, dtype=np.float64)
    bucket = int(np.clip(value, 0, 255) / (256 / CHANNELS))
    hist[min(bucket, CHANNELS - 1)] = 1.0
    # Soft neighbors so similar colors still match a little.
    if bucket > 0:
        hist[bucket - 1] = 0.35
    if bucket < CHANNELS - 1:
        hist[bucket + 1] = 0.35
    hist /= hist.sum()
    return hist


def color_from_name(name: str) -> tuple[int, int, int]:
    digest = hashlib.sha256(name.encode("utf-8")).digest()
    return digest[0], digest[1], digest[2]


def visual_fingerprint(
    color_rgb: tuple[int, int, int],
    category: str,
    extra_noise: np.ndarray | None = None,
) -> np.ndarray:
    r, g, b = color_rgb
    hist = np.concatenate([_channel_hist(r), _channel_hist(g), _channel_hist(b)])
    cats = list(CATEGORIES.keys())
    one_hot = np.zeros(CATEGORY_DIM, dtype=np.float64)
    if category in cats:
        one_hot[cats.index(category)] = 1.0
    vec = np.concatenate([hist, one_hot])
    if extra_noise is not None:
        vec = np.clip(vec + extra_noise, 0.0, 1.0)
    norm = np.linalg.norm(vec)
    return vec / norm if norm else vec


def visual_similarity(a: np.ndarray, b: np.ndarray) -> float:
    a = np.asarray(a, dtype=np.float64).ravel()
    b = np.asarray(b, dtype=np.float64).ravel()
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.clip(np.dot(a, b) / denom, 0.0, 1.0))


def _rgb_histogram(arr: np.ndarray, bins: int = 6) -> np.ndarray:
    quant = np.clip((arr / 256.0 * bins).astype(np.int32), 0, bins - 1)
    idx = quant[..., 0] * bins * bins + quant[..., 1] * bins + quant[..., 2]
    hist = np.bincount(idx.ravel(), minlength=bins**3).astype(np.float64)
    total = hist.sum()
    return hist / total if total else hist


def _spatial_means(arr: np.ndarray, grid: int = 2) -> np.ndarray:
    h, w, _ = arr.shape
    cells: list[np.ndarray] = []
    for gy in range(grid):
        for gx in range(grid):
            y0, y1 = h * gy // grid, h * (gy + 1) // grid
            x0, x1 = w * gx // grid, w * (gx + 1) // grid
            patch = arr[y0:y1, x0:x1]
            if patch.size == 0:
                cells.append(np.zeros(3, dtype=np.float64))
            else:
                cells.append(patch.reshape(-1, 3).mean(axis=0) / 255.0)
    return np.concatenate(cells)


def fingerprint_from_array(arr: np.ndarray) -> np.ndarray:
    """Appearance vector from an RGB uint8 image. Independent of the 32-d demo vector."""
    if arr.ndim != 3 or arr.shape[2] != 3:
        raise ValueError("Expected HxWx3 RGB image")
    vec = np.concatenate([_rgb_histogram(arr), _spatial_means(arr, grid=2)])
    norm = np.linalg.norm(vec)
    return vec / norm if norm else vec


def load_rgb(data: bytes, max_side: int = 192) -> np.ndarray:
    from io import BytesIO

    from PIL import Image

    image = Image.open(BytesIO(data)).convert("RGB")
    image.thumbnail((max_side, max_side))
    return np.asarray(image, dtype=np.uint8)


def fingerprint_from_bytes(data: bytes) -> np.ndarray:
    return fingerprint_from_array(load_rgb(data))


def crop_windows(arr: np.ndarray) -> list[np.ndarray]:
    """Full frame, center crop, and a 3x3 grid so a small object can still match."""
    windows = [arr]
    h, w, _ = arr.shape
    y0, y1 = h // 5, h - h // 5
    x0, x1 = w // 5, w - w // 5
    if y1 > y0 and x1 > x0:
        windows.append(arr[y0:y1, x0:x1])
    for gy in range(3):
        for gx in range(3):
            yy0, yy1 = h * gy // 3, h * (gy + 1) // 3
            xx0, xx1 = w * gx // 3, w * (gx + 1) // 3
            patch = arr[yy0:yy1, xx0:xx1]
            if patch.size >= 3 * 8 * 8:
                windows.append(patch)
    return windows


def best_photo_match(reference: np.ndarray, scene: np.ndarray) -> float:
    scores = [visual_similarity(reference, fingerprint_from_array(win)) for win in crop_windows(scene)]
    return max(scores) if scores else 0.0


def material_cues_from_array(arr: np.ndarray) -> dict[str, float | str]:
    """Cheap HSV cues, not a spectrometer. Used only as a hint next to the enrolled material."""
    rgb = arr.astype(np.float64) / 255.0
    maxc = rgb.max(axis=2)
    minc = rgb.min(axis=2)
    sat = np.divide(maxc - minc, maxc, out=np.zeros_like(maxc), where=maxc > 1e-6)
    val = maxc
    mean_s = float(sat.mean())
    mean_v = float(val.mean())
    if mean_s < 0.22 and mean_v > 0.42:
        family = "metal"
        note = "Az doyma, parlaq — metal/şüşəyə oxşayır"
    elif 0.08 < mean_s < 0.55 and 0.15 < mean_v < 0.55:
        family = "organic"
        note = "Orta doyma — dəri/ağac/parçaya oxşaya bilər"
    else:
        family = "polymer"
        note = "Rəngli plastik və ya qarışıq səth kimi görünür"
    return {"family": family, "saturation": round(mean_s, 3), "value": round(mean_v, 3), "note": note}
