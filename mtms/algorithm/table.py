"""Build the full MTMS lookup table with 512 cases (T=4, w∈{0,1}).

Ported from world_settings.gd → _build_multitype_table().

Structure: table[case_index] = [block0, block1, block2, block3]
  block_i = [tri0, tri1, tri2]
  tri = [vertex_a, vertex_b, vertex_c]

Vertex indices 0..11:
  0-3:  corners (v0=top-left, v1=top-right, v2=bot-right, v3=bot-left)
  4-7:  edge midpoints (4=top, 5=right, 6=bottom, 7=left)
  8-11: diagonal interpolation points
"""
from __future__ import annotations

from mtms.algorithm.types import MTMSCase


def build_mtms_table(num_types: int = 4) -> dict[int, MTMSCase]:
    """Generate lookup table of all possible cases.

    case_index = v0 + v1*T + v2*T^2 + v3*T^3 + w*T^4
               = v0 + 4*v1 + 16*v2 + 64*v3 + 256*w

    Returns a dict mapping each case_index (0..511) to its 4-block triangle data.
    """
    T = num_types
    cases_per_w = T ** 4  # 256
    empty_tri = [0, 0, 0]

    table: dict[int, MTMSCase] = {}

    for w in range(2):
        for v0 in range(T):
            for v1 in range(T):
                for v2 in range(T):
                    for v3 in range(T):
                        vals = [v0, v1, v2, v3]
                        ci = v0 + v1 * T + v2 * T * T + v3 * T * T * T + w * cases_per_w
                        b: list[list[list[int]]] = [
                            [list(empty_tri), list(empty_tri), list(empty_tri)]
                            for _ in range(4)
                        ]
                        uq = len(set(vals))

                        if uq == 1:
                            # All vertices same material → fill square
                            b[0] = [[0, 1, 3], [3, 1, 2], list(empty_tri)]

                        elif (uq == 2
                              and vals[0] != vals[2]
                              and vals[1] != vals[3]):
                            # Checkerboard pattern
                            if vals[0] == vals[1]:
                                b[0] = [[0, 1, 5], [0, 5, 7], list(empty_tri)]
                                b[2] = [[2, 3, 7], [2, 7, 5], list(empty_tri)]
                            else:
                                b[1] = [[1, 2, 6], [1, 6, 4], list(empty_tri)]
                                b[3] = [[3, 0, 4], [3, 4, 6], list(empty_tri)]

                        elif vals[0] == vals[1] and vals[1] == vals[2]:
                            if w == 0:
                                b[1] = [[0, 1, 7], [7, 1, 6], [6, 1, 2]]
                                b[3] = [[3, 7, 6], list(empty_tri), list(empty_tri)]
                            else:
                                b[0] = [[0, 11, 7], [0, 1, 11], list(empty_tri)]
                                b[2] = [[2, 6, 11], [2, 11, 1], list(empty_tri)]
                                b[3] = [[6, 3, 11], [11, 3, 7], list(empty_tri)]

                        elif vals[3] == vals[1] and vals[1] == vals[2]:
                            if w == 0:
                                b[0] = [[0, 8, 7], [0, 4, 8], list(empty_tri)]
                                b[1] = [[1, 8, 4], [1, 2, 8], list(empty_tri)]
                                b[3] = [[3, 7, 8], [3, 8, 2], list(empty_tri)]
                            else:
                                b[0] = [[0, 4, 7], list(empty_tri), list(empty_tri)]
                                b[2] = [[2, 3, 7], [2, 7, 4], [2, 4, 1]]

                        elif vals[3] == vals[0] and vals[0] == vals[2]:
                            if w == 0:
                                b[1] = [[1, 5, 4], list(empty_tri), list(empty_tri)]
                                b[3] = [[3, 0, 4], [3, 4, 5], [3, 5, 2]]
                            else:
                                b[0] = [[0, 4, 9], [0, 9, 3], list(empty_tri)]
                                b[1] = [[1, 5, 9], [1, 9, 4], list(empty_tri)]
                                b[2] = [[2, 9, 5], [2, 3, 9], list(empty_tri)]

                        elif vals[3] == vals[0] and vals[0] == vals[1]:
                            if w == 0:
                                b[0] = [[0, 1, 5], [0, 5, 6], [0, 6, 3]]
                                b[2] = [[2, 6, 5], list(empty_tri), list(empty_tri)]
                            else:
                                b[1] = [[1, 5, 10], [1, 10, 0], list(empty_tri)]
                                b[2] = [[2, 6, 10], [2, 10, 5], list(empty_tri)]
                                b[3] = [[3, 10, 6], [3, 0, 10], list(empty_tri)]

                        else:
                            # General case — most complex triangulation
                            if w == 0:
                                b[0] = [[7, 0, 8], [8, 0, 4], list(empty_tri)]
                                b[1] = [[4, 1, 8], [8, 1, 10], [10, 1, 5]]
                                b[2] = [[5, 2, 10], [10, 2, 6], list(empty_tri)]
                                b[3] = [[6, 3, 10], [10, 3, 8], [8, 3, 7]]
                            else:
                                b[0] = [[4, 9, 0], [0, 9, 11], [0, 11, 7]]
                                b[1] = [[4, 1, 9], [9, 1, 5], list(empty_tri)]
                                b[2] = [[5, 2, 9], [9, 2, 11], [2, 6, 11]]
                                b[3] = [[6, 3, 11], [11, 3, 7], list(empty_tri)]

                        # Convert to tuples for immutability
                        table[ci] = tuple(
                            tuple(tuple(tri) for tri in block) for block in b
                        )
    return table
