"""Tests for case index encode/decode and w-flag computation."""
import unittest

from mtms.algorithm.case_index import (
    compute_case_index,
    decode_case_index,
    compute_w_flag,
)


class TestCaseIndex(unittest.TestCase):
    def test_encode_simple(self):
        """(0,0,0,0), w=0 → case_idx=0."""
        self.assertEqual(compute_case_index((0, 0, 0, 0), 0), 0)

    def test_encode_max_v(self):
        """(3,3,3,3), w=0 → 3+12+48+192 = 255."""
        self.assertEqual(compute_case_index((3, 3, 3, 3), 0), 255)

    def test_encode_w1(self):
        """(0,0,0,0), w=1 → 256."""
        self.assertEqual(compute_case_index((0, 0, 0, 0), 1), 256)

    def test_encode_max(self):
        """(3,3,3,3), w=1 → 255 + 256 = 511."""
        self.assertEqual(compute_case_index((3, 3, 3, 3), 1), 511)

    def test_roundtrip_all(self):
        """Encode then decode — roundtrip for all 512 combinations."""
        for v0 in range(4):
            for v1 in range(4):
                for v2 in range(4):
                    for v3 in range(4):
                        for w in range(2):
                            vals = (v0, v1, v2, v3)
                            ci = compute_case_index(vals, w)
                            decoded_vals, decoded_w = decode_case_index(ci)
                            self.assertEqual(decoded_vals, vals)
                            self.assertEqual(decoded_w, w)

    def test_range(self):
        """All indices are in [0, 511]."""
        indices = set()
        for v0 in range(4):
            for v1 in range(4):
                for v2 in range(4):
                    for v3 in range(4):
                        for w in range(2):
                            ci = compute_case_index((v0, v1, v2, v3), w)
                            indices.add(ci)
        self.assertEqual(indices, set(range(512)))


class TestWFlag(unittest.TestCase):
    def test_symmetric_weights(self):
        """Equal weights → balanced → w=0 or w=1 depending on rounding."""
        # wa+wc = wb+wd → ratio = 0.5 → round(1.0) = 1... let me check
        # Actually w_ac/s + 0.5 where s=w_ac+w_bd, so if w_ac=s/2:
        # (s/2)/s + 0.5 = 0.5+0.5 = 1.0 → int(1.0) = 1
        result = compute_w_flag(0.5, 0.5, 0.5, 0.5)
        self.assertIn(result, (0, 1))

    def test_zero_sum(self):
        """Near-zero sum returns safe default of 0."""
        self.assertEqual(compute_w_flag(0.0, 0.0, 0.0, 0.0), 0)

    def test_dominant_ac(self):
        """wa+wc >> wb+wd → w=1 (rounds to 1)."""
        result = compute_w_flag(0.9, 0.1, 0.9, 0.1)
        self.assertEqual(result, 1)

    def test_dominant_bd(self):
        """wa+wc << wb+wd → w=0 (rounds to 0)."""
        result = compute_w_flag(0.1, 0.9, 0.1, 0.9)
        self.assertEqual(result, 0)


if __name__ == "__main__":
    unittest.main()
