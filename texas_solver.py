"""Utility functions for running TexasSolver from Python."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Iterable

DEFAULT_EXE_DIR = Path("TexasSolver-v0.2.0-Windows")


def run_console_solver(
    param_file: Path | str,
    *,
    exe_dir: Path | str = DEFAULT_EXE_DIR,
    use_wine: bool | None = None,
    timeout: int | None = None,
) -> str:
    """Run ``console_solver.exe`` with the given parameter file.

    Parameters
    ----------
    param_file : Path or str
        Path to the solver parameter file.
    exe_dir : Path or str, optional
        Directory containing ``console_solver.exe``. Defaults to
        ``TexasSolver-v0.2.0-Windows`` in the repository root.
    use_wine : bool, optional
        Force using ``wine`` to execute the solver. By default, this is
        automatically chosen based on the current platform.
    timeout : int, optional
        Timeout in seconds passed to :func:`subprocess.run`.

    Returns
    -------
    str
        The raw text output from the solver.
    """

    param_path = Path(param_file)
    exe_directory = Path(exe_dir)
    exe = exe_directory / "console_solver.exe"

    if use_wine is None:
        use_wine = sys.platform != "win32"

    cmd = [str(exe), str(param_path)]
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
    """Create a minimal parameter file for a heads-up flop spot."""

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


def parse_solver_output(output: str, hero_hand: str) -> tuple[str, int]:
    """Return the highest frequency action from solver output."""

    try:
        data = json.loads(output)
        actions = data["strategy"]["actions"]
        combos = data["strategy"]["strategy"]
    except Exception:  # pragma: no cover - invalid JSON
        return "check", 0

    key = hero_hand
    if key not in combos:
        key = key[2:] + key[:2]
    if key not in combos:
        return "check", 0

    dist = combos[key]
    idx = dist.index(max(dist))
    raw = actions[idx]
    parts = raw.split()

    name = parts[0].lower()
    amount = 0
    if len(parts) > 1:
        try:
            amount = int(float(parts[1]))
        except ValueError:
            amount = 0
    return name, amount
