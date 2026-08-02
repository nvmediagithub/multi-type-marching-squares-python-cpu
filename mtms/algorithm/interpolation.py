"""12-point interpolation for a single MTMS cell.

Interpolation point indices (0..11):
  0-3:  corner vertices   (v0=top-left, v1=top-right, v2=bot-right, v3=bot-left)
  4-7:  edge intersections (4=top, 5=right, 6=bottom, 7=left)
  8-11: diagonal points    (8=v0→center, 9=v1→center, 10=v2→center, 11=v3→center)

Ported from mc_3d_build.glsl.
"""
from __future__ import annotations

from mtms.algorithm.types import Point2D


def lerp2d(a: Point2D, b: Point2D, t: float) -> Point2D:
    """Linear interpolation between two 2D points."""
    return (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]))


def edge_interp(a: Point2D, b: Point2D, wa: float, wb: float) -> Point2D:
    """Weight-based interpolation along an edge.

    The intersection point divides the edge proportional to the vertex weights.
    """
    s = wa + wb
    t = wb / s if abs(s) > 1e-12 else 0.5
    return lerp2d(a, b, t)


def compute_12_points(
    cx: int, cy: int,
    wa: float, wb: float, wc: float, wd: float,
) -> list[Point2D]:
    """Compute the 12 interpolation points for a grid cell.

    Args:
        cx, cy: Integer grid coordinates of the cell (top-left corner).
        wa, wb, wc, wd: Height/weight values at corners A(top-left),
                         B(top-right), C(bot-right), D(bot-left).

    Returns:
        List of 12 Point2D values indexed by vertex index 0..11.
    """
    pts: list[Point2D] = [None, None, None, None, None, None,
                          None, None, None, None, None, None]

    # Corner vertices
    pts[0] = (float(cx), float(cy))         # v0: top-left
    pts[1] = (float(cx + 1), float(cy))     # v1: top-right
    pts[2] = (float(cx + 1), float(cy + 1)) # v2: bot-right
    pts[3] = (float(cx), float(cy + 1))     # v3: bot-left

    center: Point2D = (cx + 0.5, cy + 0.5)

    # Edge intersections
    pts[4] = edge_interp(pts[0], pts[1], wa, wb)   # top
    pts[5] = edge_interp(pts[1], pts[2], wb, wc)   # right
    pts[6] = edge_interp(pts[2], pts[3], wc, wd)   # bottom
    pts[7] = edge_interp(pts[3], pts[0], wd, wa)   # left

    # Diagonal interpolation points
    w_ac = wa + wc
    w_bd = wb + wd
    s = w_ac + w_bd
    t_bd = w_bd / s if abs(s) > 1e-12 else 0.5
    t_ac = w_ac / s if abs(s) > 1e-12 else 0.5

    pts[8]  = lerp2d(pts[0], center, t_bd)   # v0 → center
    pts[9]  = lerp2d(pts[1], center, t_ac)   # v1 → center
    pts[10] = lerp2d(pts[2], center, t_bd)   # v2 → center
    pts[11] = lerp2d(pts[3], center, t_ac)   # v3 → center

    return pts  # type: ignore[return-value]
