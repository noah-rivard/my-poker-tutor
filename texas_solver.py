from __future__ import annotations

import json
import os
import subprocess
from typing import Any, Dict


def simple_parameter_file(board: str, ranges: str, out_dir: str) -> str:
    """Create a basic parameter file for console_solver.exe."""
    os.makedirs(out_dir, exist_ok=True)
    params = {
        "board": board,
        "ranges": ranges,
        "output": os.path.join(out_dir, "solver_output.json"),
    }
    param_path = os.path.join(out_dir, "params.json")
    with open(param_path, "w", encoding="utf-8") as fh:
        json.dump(params, fh)
    return param_path


def run_console_solver(param_file: str, solver_dir: str = "TexasSolver-v0.2.0-Windows") -> subprocess.CompletedProcess:
    """Invoke console_solver.exe with the supplied parameter file."""
    exe = os.path.join(solver_dir, "console_solver.exe")
    return subprocess.run([exe, param_file], capture_output=True, text=True)


def parse_solver_output(output_json: str) -> Dict[str, Any]:
    """Return the parsed JSON output from the solver."""
    with open(output_json, encoding="utf-8") as fh:
        return json.load(fh)
