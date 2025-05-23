import json
import unittest

from config import engine_from_config
from engine import PokerEngine


class TestPokerEngine(unittest.TestCase):
    def test_hand_progression(self):
        eng = PokerEngine(num_players=3, starting_stack=100, sb_amt=1, bb_amt=2)
        eng.new_hand()

        # pre-flop actions until the engine moves to the flop
        while eng.stage == "preflop":
            if eng.turn == eng.bb:
                eng.player_action("check")
            else:
                eng.player_action("call")
        self.assertEqual(eng.stage, "flop")
        self.assertEqual(eng.pot, 6)

        # flop
        while eng.stage == "flop":
            eng.player_action("check")
        self.assertEqual(eng.stage, "turn")

        # turn
        while eng.stage == "turn":
            eng.player_action("check")
        self.assertEqual(eng.stage, "river")

        # river -> complete
        while eng.stage == "river":
            eng.player_action("check")
        self.assertEqual(eng.stage, "complete")
        self.assertEqual(sum(eng.stacks), 300)

        # history should contain one hand with recorded actions
        self.assertEqual(len(eng.hand_histories), 1)
        history = eng.hand_histories[0]
        self.assertIn("winners", history)
        self.assertIsInstance(history["winners"], list)
        for rec in history["winners"]:
            self.assertIn("hand", rec)
        self.assertIn("actions", history)

    def test_fold_to_single_player(self):
        eng = PokerEngine(num_players=2, starting_stack=100, sb_amt=1, bb_amt=2)
        eng.new_hand()

        # small blind folds preflop, big blind should win the pot
        eng.player_action("fold")
        self.assertEqual(eng.stage, "complete")
        self.assertEqual(eng.stacks[eng.bb], 101)
        history = eng.hand_histories[0]
        self.assertIsNone(history["winners"][0]["hand"])

    def test_engine_from_config(self):
        pass

    def test_side_pot(self):
        eng = PokerEngine(num_players=2, starting_stack=5, sb_amt=1, bb_amt=2)
        eng.new_hand()

        # seat 0 raises all-in preflop
        eng.player_action("raise", 3)  # call 2 + raise 3 -> total 5
        eng.player_action("call")  # seat 1 calls remaining 3
        self.assertEqual(eng.stage, "complete")
        self.assertEqual(sum(eng.stacks), 10)
        # ensure winning hand label recorded
        history = eng.hand_histories[0]
        for rec in history["winners"]:
            self.assertIsNotNone(rec["hand"]) 

        path = "temp_config.json"
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(
                {"num_players": 2, "starting_stack": 200, "sb_amt": 1, "bb_amt": 2}, fh
            )

        eng = engine_from_config(path)
        self.assertEqual(eng.num_players, 2)
        self.assertEqual(eng.starting_stack, 200)

        import os

        os.remove(path)

    def test_partial_raise_does_not_lower_current_bet(self):
        """Short all-in raise should not change the current bet."""
        eng = PokerEngine(num_players=3, starting_stack=50, sb_amt=1, bb_amt=2)
        eng.new_hand()

        eng.player_action("raise", 100)
        self.assertEqual(eng.current_bet, eng.bb_amt)
        self.assertEqual(eng.turn, eng.sb)

        eng.player_action("call")
        self.assertEqual(eng.stage, "flop")


if __name__ == "__main__":
    unittest.main()
