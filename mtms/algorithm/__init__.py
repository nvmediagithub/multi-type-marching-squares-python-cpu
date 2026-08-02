"""MTMS algorithm public API."""
from mtms.algorithm.table import build_mtms_table
from mtms.algorithm.normalization import normalize_materials
from mtms.algorithm.case_index import (
    compute_case_index,
    decode_case_index,
    compute_w_flag,
)
from mtms.algorithm.interpolation import (
    compute_12_points,
    lerp2d,
    edge_interp,
)
from mtms.algorithm.types import (
    CaseEntry,
    Triangle,
    Block,
    MTMSCase,
    VertexIndex,
    Point2D,
    EMPTY_TRIANGLE,
)

__all__ = [
    "build_mtms_table",
    "normalize_materials",
    "compute_case_index",
    "decode_case_index",
    "compute_w_flag",
    "compute_12_points",
    "lerp2d",
    "edge_interp",
    "CaseEntry",
    "Triangle",
    "Block",
    "MTMSCase",
    "VertexIndex",
    "Point2D",
    "EMPTY_TRIANGLE",
]
