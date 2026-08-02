"""Tests for 12-point interpolation."""
import unittest

from mtms.algorithm.interpolation import compute_12_points, lerp2d, edge_interp


class TestLerp(unittest.TestCase):
    def test_midpoint(self):
        m = lerp2d((0.0, 0.0), (10.0, 10.0), 0.5)
        self.assertAlmostEqual(m[0], 5.0)
        self.assertAlmostEqual(m[1], 5.0)

    def test_endpoints(self):
        a = (3.0, 7.0)
        b = (9.0, 1.0)
        self.assertAlmostEqual(lerp2d(a, b, 0.0)[0], a[0])
        self.assertAlmostEqual(lerp2d(a, b, 1.0)[0], b[0])


class TestEdgeInterp(unittest.TestCase):
    def test_equal_weights(self):
        m = edge_interp((0.0, 0.0), (1.0, 0.0), 0.5, 0.5)
        self.assertAlmostEqual(m[0], 0.5)

    def test_zero_sum_fallback(self):
        """When both weights are 0 → t=0.5."""
        m = edge_interp((0.0, 0.0), (2.0, 0.0), 0.0, 0.0)
        self.assertAlmostEqual(m[0], 1.0)


class TestCompute12Points(unittest.TestCase):
    def test_count(self):
        pts = compute_12_points(0, 0, 0.3, 0.5, 0.7, 0.4)
        self.assertEqual(len(pts), 12)

    def test_corners(self):
        pts = compute_12_points(1, 2, 0.3, 0.6, 0.9, 0.2)
        self.assertEqual(pts[0], (1.0, 2.0))     # top-left
        self.assertEqual(pts[1], (2.0, 2.0))     # top-right
        self.assertEqual(pts[2], (2.0, 3.0))     # bot-right
        self.assertEqual(pts[3], (1.0, 3.0))     # bot-left

    def test_edge_on_edges(self):
        """Edge intersection points must lie on the cell edges."""
        pts = compute_12_points(0, 0, 0.3, 0.6, 0.9, 0.2)
        # top edge (4): y=0
        self.assertAlmostEqual(pts[4][1], 0.0)
        # right edge (5): x=1
        self.assertAlmostEqual(pts[5][0], 1.0)
        # bottom edge (6): y=1
        self.assertAlmostEqual(pts[6][1], 1.0)
        # left edge (7): x=0
        self.assertAlmostEqual(pts[7][0], 0.0)

    def test_within_cell(self):
        """All 12 points must lie within the unit cell [cx,cx+1]×[cy,cy+1]."""
        pts = compute_12_points(5, 3, 0.4, 0.8, 0.1, 0.6)
        for p in pts:
            self.assertGreaterEqual(p[0], 5.0)
            self.assertLessEqual(p[0], 6.0)
            self.assertGreaterEqual(p[1], 3.0)
            self.assertLessEqual(p[1], 4.0)


if __name__ == "__main__":
    unittest.main()
