import json
import unittest
from unittest.mock import patch

from engine import PokerEngine
from ai import solver_ai_move


class TestSolverAIMove(unittest.TestCase):
    def test_parses_solver_output(self):
        eng = PokerEngine(num_players=2, starting_stack=100, sb_amt=1, bb_amt=2)
        eng.new_hand()
        seat = eng.turn
        eng.hole_cards[seat] = [(14, 2), (14, 1)]  # AhAd

        sample = json.dumps({
            "strategy": {
                "actions": ["CHECK", "BET 50"],
                "strategy": {"AhAd": [0.1, 0.9]}
            }
        })

        with patch("texas_solver.run_console_solver", return_value=sample), \
             patch("texas_solver.simple_parameter_file", return_value="dummy.txt"):
            action, amt = solver_ai_move(eng, seat, hero_range="AhAd", opp_range="random")

        self.assertEqual(action, "bet")
        self.assertEqual(amt, 50)


if __name__ == "__main__":
    unittest.main()
