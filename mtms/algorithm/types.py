"""Typed aliases and dataclasses for the MTMS algorithm domain model."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final

# Vertex indices into the 12-point interpolation array (0..11)
VertexIndex = int

# A triangle: three vertex indices
Triangle = tuple[VertexIndex, VertexIndex, VertexIndex]

# Three triangles per material block
Block = tuple[Triangle, Triangle, Triangle]

# Four blocks — one per local material type (0..3)
MTMSCase = tuple[Block, Block, Block, Block]

# 2D point as a simple alias
Point2D = tuple[float, float]


# Sentinel for empty triangle
EMPTY_TRIANGLE: Final[Triangle] = (0, 0, 0)


@dataclass(frozen=True)
class CaseEntry:
    """Fully decoded entry from the MTMS lookup table."""
    case_index: int                       # 0..511
    vertex_values: tuple[int, int, int, int]  # (v0, v1, v2, v3), each in 0..3
    w_flag: int                          # 0 or 1 — diagonal ambiguity flag
    blocks: MTMSCase                     # 4 blocks × 3 triangles
