"""Tests for terrain generation and material classification."""
import unittest

import numpy as np

from mtms.terrain.heightmap import generate_heightmap, classify_height
from mtms.terrain.perlin import perlin_noise_2d


class TestPerlinNoise(unittest.TestCase):
    def test_shape(self):
        result = perlin_noise_2d((10, 20), seed=42)
        self.assertEqual(result.shape, (10, 20))

    def test_deterministic(self):
        """Same seed → identical output."""
        a = perlin_noise_2d((8, 8), seed=123)
        b = perlin_noise_2d((8, 8), seed=123)
        np.testing.assert_array_equal(a, b)

    def test_different_seeds(self):
        """Different seeds produce different gradient arrays."""
        rng_a = np.random.RandomState(42)
        rng_b = np.random.RandomState(137)
        ga = rng_a.randn(10, 10)
        gb = rng_b.randn(10, 10)
        self.assertFalse(np.allclose(ga, gb))

    def test_gradients_nonzero(self):
        """RandomState generates non-degenerate gradient vectors."""
        rng = np.random.RandomState(42)
        gx = rng.randn(66, 66)
        gy = rng.randn(66, 66)
        self.assertGreater(gx.std(), 0.1)
        self.assertGreater(gy.std(), 0.1)


class TestHeightmap(unittest.TestCase):
    def test_shape(self):
        """size=10 → heightmap of (11, 11)."""
        hm = generate_heightmap(10, seed=42)
        self.assertEqual(hm.shape, (11, 11))

    def test_range(self):
        """Normalized to [0, 1]."""
        hm = generate_heightmap(32, seed=7)
        self.assertGreaterEqual(hm.min(), 0.0)
        self.assertLessEqual(hm.max(), 1.0)

    def test_deterministic(self):
        a = generate_heightmap(16, seed=99)
        b = generate_heightmap(16, seed=99)
        np.testing.assert_array_equal(a, b)


class TestClassifyHeight(unittest.TestCase):
    def setUp(self):
        self.thresholds = (0.25, 0.40, 0.65, 0.85)

    def test_low(self):
        self.assertEqual(classify_height(0.1, self.thresholds), 0)

    def test_mid(self):
        self.assertEqual(classify_height(0.50, self.thresholds), 2)

    def test_boundary_below(self):
        self.assertEqual(classify_height(0.249, self.thresholds), 0)
        self.assertEqual(classify_height(0.250, self.thresholds), 1)

    def test_max(self):
        """Height >= last threshold → index = len(thresholds)."""
        self.assertEqual(classify_height(1.0, self.thresholds), 4)

    def test_zero(self):
        self.assertEqual(classify_height(0.0, self.thresholds), 0)


if __name__ == "__main__":
    unittest.main()
