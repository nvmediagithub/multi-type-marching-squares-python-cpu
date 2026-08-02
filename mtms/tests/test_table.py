"""Tests for MTMS lookup table generation."""
import unittest

from mtms.algorithm.table import build_mtms_table


class TestTableGeneration(unittest.TestCase):
    def setUp(self):
        self.table = build_mtms_table(num_types=4)

    def test_total_cases(self):
        """T=4 → 4^4 × 2 (w∈{0,1}) = 512 cases."""
        self.assertEqual(len(self.table), 512)

    def test_uniform_case_all_zero(self):
        """case_idx=0: all vertices type 0 → filled with two triangles."""
        entry = self.table[0]
        # block[0] should have the fill triangles
        self.assertEqual(entry[0][0], (0, 1, 3))
        self.assertEqual(entry[0][1], (3, 1, 2))

    def test_uniform_case_all_3(self):
        """case with v0=v1=v2=v3=3 → all type 3."""
        # ci = 3 + 3*4 + 3*16 + 3*64 = 255
        entry = self.table[255]
        self.assertEqual(entry[0][0], (0, 1, 3))
        self.assertEqual(entry[0][1], (3, 1, 2))

    def test_empty_blocks(self):
        """Blocks that don't own a region should have empty triangles."""
        entry = self.table[0]
        # block 1..3 should be all zeros
        for bi in range(1, 4):
            for tri in entry[bi]:
                self.assertEqual(tri, (0, 0, 0))

    def test_structure_four_blocks(self):
        """Each entry has exactly 4 blocks."""
        for ci, entry in self.table.items():
            self.assertEqual(len(entry), 4)

    def test_block_three_triangles(self):
        """Each block has exactly 3 triangle slots."""
        for ci, entry in self.table.items():
            for block in entry:
                self.assertEqual(len(block), 3)

    def test_vertex_indices_in_range(self):
        """Triangle vertex indices must be in [0, 11]."""
        for ci, entry in self.table.items():
            for block in entry:
                for tri in block:
                    for vi in tri:
                        self.assertTrue(0 <= vi <= 11)

    def test_w_flag_separation(self):
        """w=0 cases are 0..255, w=1 cases are 256..511."""
        for ci in range(256):
            self.assertIn(ci, self.table)
        for ci in range(256, 512):
            self.assertIn(ci, self.table)


if __name__ == "__main__":
    unittest.main()
