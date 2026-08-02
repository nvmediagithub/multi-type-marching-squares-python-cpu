"""Material normalization — sequential modular arithmetic.

Maps global material IDs (0..4 for 5 terrain types) to local IDs (0..3)
so that the MTMS lookup table (which has T=4) can be used with 5+ global
types. Ported from mc_3d_build.glsl.
"""
from __future__ import annotations

from typing import Sequence


def normalize_materials(global_ids: Sequence[int]) -> list[int]:
    """Reduce a list of global material IDs to local 0..T-1 IDs.

    Uses iterative modular arithmetic: at each step, compute n % max(nums)
    with an offset, reducing the range until all values fit in [0, T-1].
    """
    nums = [g + 1 for g in global_ids]
    for _ in range(4):
        mx = max(nums)
        if mx <= 0:
            break
        nums = [n % mx + 1 for n in nums]
    mx = max(nums)
    if mx > 0:
        nums = [n % mx for n in nums]
    return nums
