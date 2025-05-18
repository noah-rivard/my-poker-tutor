import unittest

from hand_strength_simple import monte_carlo_strength


class TestMonteCarloStrength(unittest.TestCase):
    def test_strength_bounds(self):
        strength = monte_carlo_strength(["As", "Ac"], iterations=500, seed=42)
        self.assertGreaterEqual(strength, 0)
        self.assertLessEqual(strength, 1)
        # AA heads-up preflop should win around 87% of the time
        self.assertGreater(strength, 0.8)
        self.assertLess(strength, 0.95)


if __name__ == "__main__":
    unittest.main()
