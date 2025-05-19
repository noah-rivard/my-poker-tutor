import unittest

from engine import PokerEngine
from ai import optimal_ai_move


class TestOptimalAIMove(unittest.TestCase):
    def test_returns_valid_action(self):
        eng = PokerEngine(num_players=2, starting_stack=100, sb_amt=1, bb_amt=2)
        eng.new_hand()
        seat = eng.turn
        action, amount = optimal_ai_move(eng, seat, sample_count=20)
        self.assertIn(action, {"fold", "check", "call", "bet", "raise"})
        if action in {"bet", "raise"}:
            self.assertGreaterEqual(amount, 1)
        else:
            self.assertEqual(amount, 0)


if __name__ == "__main__":
    unittest.main()
