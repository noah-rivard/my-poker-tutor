import json
import os
import tempfile
import unittest
from unittest.mock import patch

from pathlib import Path
from engine import PokerEngine
import texas_solver


class TestTexasSolverUtils(unittest.TestCase):
    def test_simple_parameter_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out = os.path.join(tmpdir, "params.txt")
            path = texas_solver.simple_parameter_file(
                pot=100,
                stack=50,
                board=["Ah", "Kd", "2c"],
                range_oop="random",
                range_ip="random",
                output_path=out,
            )
            text = Path(path).read_text().splitlines()
            self.assertIn("set_pot 100", text)
            self.assertIn("set_effective_stack 50", text)
            self.assertIn("set_board Ah,Kd,2c", text)
            self.assertIn("set_range_oop random", text)
            self.assertIn("set_range_ip random", text)
            self.assertTrue(text[-1].startswith("build_tree"))

    def test_engine_parameter_file(self):
        eng = PokerEngine(
            num_players=2,
            starting_stack=100,
            sb_amt=1,
            bb_amt=2,
        )
        eng.new_hand()
        with tempfile.TemporaryDirectory() as tmpdir:
            out = os.path.join(tmpdir, "params.json")
            path = texas_solver.engine_parameter_file(eng, eng.turn, out)
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            self.assertEqual(data["hero_seat"], eng.turn)
            self.assertIn("0", data["holes"])
            self.assertEqual(data["pot"], eng.pot)

    def test_launch_solver_gui_passes_param(self):
        with patch("texas_solver.subprocess.Popen") as popen, patch(
            "texas_solver.sys.platform",
            "win32",
        ):
            texas_solver.launch_solver_gui(
                exe_dir="C:/solver",
                param_file="spot.json",
            )
            popen.assert_called_once_with([
                "C:/solver/TexasSolverGui.exe",
                "spot.json",
            ])


if __name__ == "__main__":
    unittest.main()
