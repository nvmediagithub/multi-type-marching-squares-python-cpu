"""Tests for material normalization."""
import unittest

from mtms.algorithm.normalization import normalize_materials


class TestNormalization(unittest.TestCase):
    def test_identical_inputs(self):
        """[2, 2, 2, 2] → [0, 0, 0, 0] (all same)."""
        self.assertEqual(normalize_materials([2, 2, 2, 2]), [0, 0, 0, 0])

    def test_all_zero(self):
        """[0, 0, 0, 0] → [0, 0, 0, 0]."""
        self.assertEqual(normalize_materials([0, 0, 0, 0]), [0, 0, 0, 0])

    def test_sequence_0123(self):
        """[0, 1, 2, 3] — distinct values should normalize to compact range."""
        result = normalize_materials([0, 1, 2, 3])
        for v in result:
            self.assertTrue(0 <= v <= 3)

    def test_reverse_sequence(self):
        """[3, 2, 1, 0] — should produce valid normalized values."""
        result = normalize_materials([3, 2, 1, 0])
        for v in result:
            self.assertTrue(0 <= v <= 3)

    def test_five_types(self):
        """[4, 3, 2, 1] — 5 global types compressed to 0..3."""
        result = normalize_materials([4, 3, 2, 1])
        for v in result:
            self.assertTrue(0 <= v <= 3)

    def test_output_length(self):
        """Output has the same length as input."""
        for inp in [[0], [0, 1], [0, 0, 0, 0], [4, 3, 2, 1, 0]]:
            result = normalize_materials(inp)
            self.assertEqual(len(result), len(inp))


if __name__ == "__main__":
    unittest.main()
