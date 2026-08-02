"""Material type definitions and palette for terrain rendering."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum


class MaterialType(IntEnum):
    """Five global terrain material types."""
    WATER = 0
    SAND = 1
    GRASS = 2
    ROCKS = 3
    SNOW = 4


@dataclass(frozen=True)
class MaterialPalette:
    """Color, name, and threshold mapping for all materials."""
    colors: list[tuple[int, int, int]] = field(default_factory=lambda: [
        (70, 150, 220),   # Water — blue
        (215, 195, 105),  # Sand — yellow
        (95, 185, 95),    # Grass — green
        (145, 143, 143),  # Rocks — grey
        (235, 235, 242),  # Snow — white
    ])
    names: list[str] = field(default_factory=lambda: [
        "Вода", "Песок", "Трава", "Скалы", "Снег"
    ])
    thresholds: tuple[float, ...] = field(
        default_factory=lambda: (0.25, 0.40, 0.65, 0.85)
    )
