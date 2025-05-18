import unittest
import json
from engine import PokerEngine
from config import engine_from_config


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
        self.assertIn("actions", history)

    def test_fold_to_single_player(self):
        eng = PokerEngine(num_players=2, starting_stack=100, sb_amt=1, bb_amt=2)
        eng.new_hand()

        # small blind folds preflop, big blind should win the pot
        eng.player_action("fold")
        self.assertEqual(eng.stage, "complete")
        self.assertEqual(eng.stacks[eng.bb], 101)

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


if __name__ == "__main__":
    unittest.main()
