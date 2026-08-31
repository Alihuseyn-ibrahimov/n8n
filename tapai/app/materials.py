"""Simulated spectral signatures and a material classifier.

The 16-band vector is a stand-in for a future hardware stack:

* bands 0-3   inductive / metal-detector response
* bands 4-7   capacitive / dielectric response
* bands 8-11  near-infrared reflectance
* bands 12-15 mmWave radar cross-section (size/shape proxy)

This is physically inspired, not a claim that a cheap gadget can uniquely
identify a specific key. Metals cluster together; leather and plastic do not.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

BANDS = 16
RNG_SEED = 42

MATERIAL_FAMILIES = {
    "brass": "metal",
    "steel": "metal",
    "aluminum": "metal",
    "leather": "organic",
    "fabric": "organic",
    "wood": "organic",
    "paper": "organic",
    "plastic": "polymer",
    "rubber": "polymer",
    "glass": "mineral",
    "ceramic": "mineral",
}

# Prototypical signatures in [0, 1]. Metals share a high inductive head.
PROTOTYPES: dict[str, np.ndarray] = {
    "brass": np.array(
        [0.92, 0.88, 0.84, 0.80, 0.10, 0.12, 0.11, 0.09, 0.55, 0.62, 0.48, 0.33, 0.22, 0.24, 0.20, 0.18],
        dtype=np.float64,
    ),
    "steel": np.array(
        [0.95, 0.93, 0.90, 0.86, 0.08, 0.09, 0.08, 0.07, 0.28, 0.30, 0.26, 0.22, 0.25, 0.27, 0.23, 0.21],
        dtype=np.float64,
    ),
    "aluminum": np.array(
        [0.88, 0.85, 0.81, 0.77, 0.11, 0.10, 0.12, 0.10, 0.70, 0.72, 0.66, 0.58, 0.30, 0.28, 0.26, 0.24],
        dtype=np.float64,
    ),
    "leather": np.array(
        [0.06, 0.07, 0.05, 0.06, 0.42, 0.48, 0.45, 0.40, 0.35, 0.28, 0.22, 0.18, 0.14, 0.13, 0.12, 0.11],
        dtype=np.float64,
    ),
    "fabric": np.array(
        [0.04, 0.05, 0.04, 0.03, 0.38, 0.44, 0.50, 0.47, 0.52, 0.48, 0.40, 0.34, 0.10, 0.09, 0.08, 0.08],
        dtype=np.float64,
    ),
    "wood": np.array(
        [0.05, 0.06, 0.05, 0.04, 0.30, 0.33, 0.31, 0.28, 0.60, 0.55, 0.42, 0.30, 0.16, 0.15, 0.14, 0.13],
        dtype=np.float64,
    ),
    "paper": np.array(
        [0.03, 0.03, 0.02, 0.02, 0.22, 0.25, 0.24, 0.21, 0.78, 0.74, 0.70, 0.66, 0.08, 0.07, 0.07, 0.06],
        dtype=np.float64,
    ),
    "plastic": np.array(
        [0.07, 0.08, 0.06, 0.07, 0.62, 0.70, 0.66, 0.58, 0.40, 0.38, 0.36, 0.33, 0.18, 0.17, 0.16, 0.15],
        dtype=np.float64,
    ),
    "rubber": np.array(
        [0.09, 0.10, 0.08, 0.09, 0.55, 0.60, 0.58, 0.52, 0.18, 0.16, 0.15, 0.14, 0.12, 0.12, 0.11, 0.10],
        dtype=np.float64,
    ),
    "glass": np.array(
        [0.12, 0.11, 0.10, 0.10, 0.20, 0.18, 0.16, 0.15, 0.15, 0.20, 0.55, 0.70, 0.35, 0.32, 0.30, 0.28],
        dtype=np.float64,
    ),
    "ceramic": np.array(
        [0.10, 0.11, 0.09, 0.10, 0.24, 0.22, 0.20, 0.18, 0.50, 0.46, 0.40, 0.36, 0.20, 0.19, 0.18, 0.17],
        dtype=np.float64,
    ),
}

AZ_MATERIAL = {
    "brass": "mis / latun",
    "steel": "polad",
    "aluminum": "alüminium",
    "leather": "dəri",
    "fabric": "parça",
    "wood": "ağac",
    "paper": "kağız",
    "plastic": "plastik",
    "rubber": "rezin",
    "glass": "şüşə",
    "ceramic": "keramika",
}

AZ_FAMILY = {
    "metal": "metal",
    "organic": "üzvi",
    "polymer": "polimer",
    "mineral": "mineral",
}


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    a = np.asarray(a, dtype=np.float64).ravel()
    b = np.asarray(b, dtype=np.float64).ravel()
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.clip(np.dot(a, b) / denom, 0.0, 1.0))


def noisy_signature(material: str, rng: np.random.Generator, noise: float = 0.045) -> np.ndarray:
    if material not in PROTOTYPES:
        raise ValueError(f"Unknown material: {material}")
    proto = PROTOTYPES[material]
    sample = proto + rng.normal(0.0, noise, size=proto.shape)
    return np.clip(sample, 0.0, 1.0)


@dataclass
class MaterialGuess:
    material: str
    family: str
    confidence: float
    probabilities: dict[str, float]


class MaterialClassifier:
    """Nearest prototype in the 16-band space. No sklearn, no training step."""

    def predict(self, spectrum: np.ndarray) -> MaterialGuess:
        scores = {label: cosine(spectrum, proto) for label, proto in PROTOTYPES.items()}
        material = max(scores, key=scores.get)
        total = sum(scores.values()) or 1.0
        return MaterialGuess(
            material=material,
            family=MATERIAL_FAMILIES[material],
            confidence=float(scores[material]),
            probabilities={label: float(score / total) for label, score in scores.items()},
        )


_classifier: MaterialClassifier | None = None


def get_classifier() -> MaterialClassifier:
    global _classifier
    if _classifier is None:
        _classifier = MaterialClassifier()
    return _classifier
