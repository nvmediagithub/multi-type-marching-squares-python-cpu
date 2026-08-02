"""Heightmap generation and material classification.

Multi-octave Perlin noise → normalized [0,1] heightmap → discrete
material types via threshold-based classification.
"""
from __future__ import annotations

import numpy as np

from mtms.terrain.perlin import perlin_noise_2d


def generate_heightmap(
    size: int,
    seed: int = 42,
    scale: float = 0.08,
    octaves: int = 4,
    persistence: float = 0.5,
) -> np.ndarray:
    """Generate a normalized heightmap via multi-octave Perlin noise.

    Args:
        size: Grid dimensions in cells (the heightmap will be (size+1)×(size+1)).
        seed: Random seed for reproducibility.
        scale: Base spatial frequency.
        octaves: Number of noise layers to sum.
        persistence: Amplitude multiplier per octave.

    Returns:
        numpy array of shape (size+1, size+1) with values in [0, 1].
    """
    h = size + 1
    hm = np.zeros((h, h), dtype=np.float64)
    amp = 1.0
    freq = 1.0

    for layer in range(octaves):
        hm += amp * perlin_noise_2d(
            (h, h), seed=seed + layer * 1000, scale=scale * freq
        )
        amp *= persistence
        freq *= 2.0

    mn, mx = hm.min(), hm.max()
    if mx - mn > 1e-9:
        hm = (hm - mn) / (mx - mn)
    return hm


def classify_height(
    h: float,
    thresholds: tuple[float, ...] = (0.25, 0.40, 0.65, 0.85),
) -> int:
    """Map a normalized height value to a material type index.

    Returns an integer in [0, len(thresholds)]. Each threshold marks the
    boundary between two consecutive material types.
    """
    for i, t in enumerate(thresholds):
        if h < t:
            return i
    return len(thresholds)
