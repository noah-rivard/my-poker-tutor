import json
import os
import subprocess
from typing import Any

from engine import PokerEngine


def simple_parameter_file(engine: PokerEngine, seat: int, path: str) -> str:
    """Write a basic parameter JSON file for ``console_solver.exe``.

    The JSON contains hole cards, board cards, stack sizes, and current bets.
    """
    data: dict[str, Any] = {
        "hero_seat": seat,
        "board": [engine._tuple_to_str(c) for c in engine.community],
        "holes": {
            str(i): [engine._tuple_to_str(c) for c in cards]
            for i, cards in engine.hole_cards.items()
        },
        "stacks": engine.stacks,
        "contributions": engine.contributions,
        "current_bet": engine.current_bet,
        "pot": engine.pot,
    }
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
    return path


def run_console_solver(param_path: str) -> str:
    """Invoke ``console_solver.exe`` using Wine and return its output."""
    exe = os.path.join(
        os.path.dirname(__file__), "TexasSolver-v0.2.0-Windows", "console_solver.exe"
    )
    cmd = ["wine", exe, param_path]
    try:
        return subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT)
    except Exception as exc:  # pragma: no cover - external process may fail
        return str(exc)
