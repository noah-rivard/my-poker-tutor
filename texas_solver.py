from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Iterable
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from engine import PokerEngine

DEFAULT_EXE_DIR = Path("TexasSolver-v0.2.0-Windows")


def run_console_solver(
    param_file: Path | str,
    *,
    exe_dir: Path | str = DEFAULT_EXE_DIR,
    use_wine: bool | None = None,
    timeout: int | None = None,
) -> str:
    """Run ``console_solver.exe`` with the supplied parameter file."""

    exe_path = Path(exe_dir) / "console_solver.exe"
    cmd = [str(exe_path), str(param_file)]

    if use_wine is None:
        use_wine = sys.platform != "win32"
    if use_wine:
        cmd.insert(0, "wine")

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=True,
    )
    return result.stdout


def simple_parameter_file(
    *,
    pot: int,
    stack: int,
    board: Iterable[str] | None,
    range_oop: str,
    range_ip: str,
    output_path: Path | str,
) -> Path:
    """Create a minimal parameter file for a heads-up spot."""

    board_str = ",".join(board) if board else ""
    lines = [
        f"set_pot {pot}",
        f"set_effective_stack {stack}",
    ]
    if board_str:
        lines.append(f"set_board {board_str}")
    lines.append(f"set_range_oop {range_oop}")
    lines.append(f"set_range_ip {range_ip}")
    lines.append("build_tree")

    path = Path(output_path)
    path.write_text("\n".join(lines))
    return path


def engine_parameter_file(engine: "PokerEngine", seat: int, path: str) -> str:
    """Write a JSON parameter file for ``console_solver.exe`` from ``engine``."""

    data = {
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
