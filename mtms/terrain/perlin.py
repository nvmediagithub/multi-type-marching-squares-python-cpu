"""Vectorized 2D Perlin noise using numpy.

No external dependencies beyond numpy — designed for terrain heightmap
generation in the MTMS viewer.
"""
from __future__ import annotations

import numpy as np


def perlin_noise_2d(
    shape: tuple[int, int],
    seed: int = 42,
    scale: float = 1.0,
) -> np.ndarray:
    """Generate a 2D Perlin noise field.

    Args:
        shape: (height, width) of the output grid.
        seed: Random seed for reproducibility.
        scale: Spatial frequency scaler.

    Returns:
        numpy array of shape `shape` with values approximately in [-1, 1].
    """
    rng = np.random.RandomState(seed)
    h, w = shape

    # Gradient vectors at each lattice node (+2 border for safe indexing)
    gx = rng.randn(h + 2, w + 2)
    gy = rng.randn(h + 2, w + 2)

    # Sample coordinates in noise space
    xs = np.arange(w, dtype=np.float64) * scale
    ys = np.arange(h, dtype=np.float64) * scale
    xx, yy = np.meshgrid(xs, ys)

    # Integer lattice positions
    xi = np.floor(xx).astype(int)
    yi = np.floor(yy).astype(int)

    # Fractional parts
    xf = xx - xi
    yf = yy - yi

    # Improved Perlin fade: 6t^5 - 15t^4 + 10t^3
    u = xf * xf * xf * (xf * (xf * 6.0 - 15.0) + 10.0)
    v = yf * yf * yf * (yf * (yf * 6.0 - 15.0) + 10.0)

    # Clamp indices to gradient array bounds
    xi = np.clip(xi, 0, h)
    yi = np.clip(yi, 0, w)

    # Dot products: g · δ
    def _dot(gx_a: np.ndarray, gy_a: np.ndarray, dx: float, dy: float) -> np.ndarray:
        return gx_a * dx + gy_a * dy

    n00 = _dot(gx[yi, xi],       gy[yi, xi],       xf,      yf)
    n10 = _dot(gx[yi, xi + 1],   gy[yi, xi + 1],   xf - 1.0, yf)
    n01 = _dot(gx[yi + 1, xi],   gy[yi + 1, xi],   xf,      yf - 1.0)
    n11 = _dot(gx[yi + 1, xi+1], gy[yi + 1, xi+1], xf - 1.0, yf - 1.0)

    # Bilinear interpolation with fade
    nx0 = n00 + u * (n10 - n00)
    nx1 = n01 + u * (n11 - n01)
    return nx0 + v * (nx1 - nx0)
