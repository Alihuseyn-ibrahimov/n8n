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
