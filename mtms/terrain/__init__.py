"""Terrain generation public API."""
from mtms.terrain.perlin import perlin_noise_2d
from mtms.terrain.heightmap import generate_heightmap, classify_height
from mtms.terrain.materials import MaterialType, MaterialPalette

__all__ = [
    "perlin_noise_2d",
    "generate_heightmap",
    "classify_height",
    "MaterialType",
    "MaterialPalette",
]
