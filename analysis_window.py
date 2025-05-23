from __future__ import annotations

import os
from typing import Optional

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QCheckBox,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ai import estimate_equity_vs_random, optimal_ai_move
from texas_solver import engine_parameter_file, launch_solver_gui
from engine import PokerEngine


class AnalysisWindow(QMainWindow):
    """Separate window displaying equity and solver information."""

    def __init__(
        self,
        engine: PokerEngine,
        seat: int,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Analysis")
        self.engine = engine
        self.seat = seat

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        self.equity_label = QLabel("Equity: N/A")
        self.optimal_label = QLabel("Recommended: N/A")
        layout.addWidget(self.equity_label, alignment=Qt.AlignCenter)
        layout.addWidget(self.optimal_label, alignment=Qt.AlignCenter)

        self.use_solver = QCheckBox("Auto-update solver")
        layout.addWidget(self.use_solver, alignment=Qt.AlignCenter)
        self.solver_label = QLabel("Solver file: N/A")
        layout.addWidget(self.solver_label, alignment=Qt.AlignCenter)

        self.launch_btn = QPushButton("Launch Solver GUI")
        self.launch_btn.clicked.connect(self._launch_solver_gui)
        layout.addWidget(self.launch_btn, alignment=Qt.AlignCenter)

    def set_context(self, engine: PokerEngine, seat: int) -> None:
        self.engine = engine
        self.seat = seat

    def refresh(self) -> None:
        self._update_stats()
        self._update_solver_params()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _update_stats(self) -> None:
        hole = self.engine.hole_cards.get(self.seat)
        if not hole:
            self.equity_label.setText("Equity: N/A")
            self.optimal_label.setText("Recommended: N/A")
            return

        hole_strs = [self.engine._tuple_to_str(c) for c in hole]
        board_strs = [
            self.engine._tuple_to_str(c) for c in self.engine.community
        ]
        active_count = sum(self.engine.active)

        try:
            eq = estimate_equity_vs_random(
                hole_strs, board_strs, active_count
            )
            self.equity_label.setText(f"Equity: {eq*100:.1f}%")
        except Exception:
            self.equity_label.setText("Equity: err")

        try:
            action, amt = optimal_ai_move(
                self.engine, self.seat, sample_count=100
            )
            if action in {"bet", "raise"}:
                self.optimal_label.setText(f"Recommended: {action} {amt}")
            else:
                self.optimal_label.setText(f"Recommended: {action}")
        except Exception:
            self.optimal_label.setText("Recommended: err")

    def _update_solver_params(self) -> None:
        if not self.use_solver.isChecked():
            return
        param_dir = os.path.join(os.path.dirname(__file__), "solver_params")
        os.makedirs(param_dir, exist_ok=True)
        path = os.path.join(param_dir, "current.json")
        engine_parameter_file(self.engine, self.seat, path)
        self.solver_label.setText(f"Solver file: {path}")

    def _launch_solver_gui(self) -> None:
        """Launch the solver GUI with the current game state."""

        param_dir = os.path.join(os.path.dirname(__file__), "solver_params")
        os.makedirs(param_dir, exist_ok=True)
        path = os.path.join(param_dir, "launch.json")
        engine_parameter_file(self.engine, self.seat, path)
        self.solver_label.setText(f"Solver file: {path}")
        launch_solver_gui(param_file=path)
