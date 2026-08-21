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
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

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
    """Random forest over synthetic spectra. Trained once at startup."""

    def __init__(self, samples_per_class: int = 80, noise: float = 0.05) -> None:
        self.labels = list(PROTOTYPES.keys())
        self.encoder = LabelEncoder()
        self.model = RandomForestClassifier(
            n_estimators=80,
            max_depth=8,
            random_state=RNG_SEED,
            n_jobs=1,
        )
        self._fit(samples_per_class, noise)

    def _fit(self, samples_per_class: int, noise: float) -> None:
        rng = np.random.default_rng(RNG_SEED)
        X: list[np.ndarray] = []
        y: list[str] = []
        for label in self.labels:
            for _ in range(samples_per_class):
                X.append(noisy_signature(label, rng, noise=noise))
                y.append(label)
        y_enc = self.encoder.fit_transform(y)
        self.model.fit(np.vstack(X), y_enc)

    def predict(self, spectrum: np.ndarray) -> MaterialGuess:
        x = np.asarray(spectrum, dtype=np.float64).reshape(1, -1)
        proba = self.model.predict_proba(x)[0]
        idx = int(np.argmax(proba))
        material = str(self.encoder.inverse_transform([idx])[0])
        probs = {
            str(self.encoder.inverse_transform([i])[0]): float(p)
            for i, p in enumerate(proba)
        }
        return MaterialGuess(
            material=material,
            family=MATERIAL_FAMILIES[material],
            confidence=float(proba[idx]),
            probabilities=probs,
        )


_classifier: MaterialClassifier | None = None


def get_classifier() -> MaterialClassifier:
    global _classifier
    if _classifier is None:
        _classifier = MaterialClassifier()
    return _classifier
