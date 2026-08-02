"""Case index computation and the w-flag for diagonal ambiguity.

case_index = v0 + v1*T + v2*T^2 + v3*T^3 + w*T^4
           = v0 + 4*v1 + 16*v2 + 64*v3 + 256*w

w-flag resolves diagonal ambiguity:
    w = round(w_ac / (w_ac + w_bd))
    where w_ac = wa + wc,  w_bd = wb + wd
"""
from __future__ import annotations


def compute_case_index(
    vertex_values: tuple[int, int, int, int],
    w_flag: int,
    num_types: int = 4,
) -> int:
    """Encode four vertex types and a w-flag into a lookup-table index.

    Returns an int in [0, num_types**4 * 2 - 1].
    """
    T = num_types
    v0, v1, v2, v3 = vertex_values
    return (v0
            + v1 * T
            + v2 * T * T
            + v3 * T * T * T
            + w_flag * (T ** 4))


def decode_case_index(
    case_idx: int,
    num_types: int = 4,
) -> tuple[tuple[int, int, int, int], int]:
    """Decode a case index back into (v0,v1,v2,v3) and w-flag."""
    T = num_types
    cases_per_w = T ** 4
    w_val = case_idx // cases_per_w
    rem = case_idx % cases_per_w

    v3 = rem // (T ** 3); rem %= T ** 3
    v2 = rem // (T ** 2); rem %= T ** 2
    v1 = rem // T
    v0 = rem % T

    return (v0, v1, v2, v3), w_val


def compute_w_flag(wa: float, wb: float, wc: float, wd: float) -> int:
    """Compute the w-flag to resolve diagonal ambiguity.

    w_ac = wa + wc  (anti-clockwise diagonal weights)
    w_bd = wb + wd  (clockwise diagonal weights)
    w = round(w_ac / (w_ac + w_bd))
    """
    w_ac = wa + wc
    w_bd = wb + wd
    s = w_ac + w_bd
    if abs(s) < 1e-12:
        return 0
    return int(w_ac / s + 0.5)
