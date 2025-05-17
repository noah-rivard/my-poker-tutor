import unittest
from engine import PokerEngine


class TestPokerEngine(unittest.TestCase):
    def test_hand_progression(self):
        eng = PokerEngine(num_players=3, starting_stack=100, sb_amt=1, bb_amt=2)
        eng.new_hand()

        # pre-flop: all players call or check
        eng.player_action("call")  # seat 0
        eng.player_action("call")  # seat 1
        eng.player_action("check")  # seat 2 (big blind)
        self.assertEqual(eng.stage, "flop")
        self.assertEqual(eng.pot, 6)

        # flop: everyone checks
        eng.player_action("check")  # seat left of button
        eng.player_action("check")
        eng.player_action("check")
        self.assertEqual(eng.stage, "turn")

        # turn: everyone checks
        eng.player_action("check")
        eng.player_action("check")
        eng.player_action("check")
        self.assertEqual(eng.stage, "river")

        # river: everyone checks -> hand complete
        eng.player_action("check")
        eng.player_action("check")
        eng.player_action("check")
        self.assertEqual(eng.stage, "complete")
        self.assertEqual(sum(eng.stacks), 300)


if __name__ == "__main__":
    unittest.main()

