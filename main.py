
import sys
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QGridLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFrame,
    QSpinBox,
    QSlider,
    QPlainTextEdit,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QColor, QFont, QPixmap
import os
import random
import sys

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QFont, QPainter, QPixmap
from PyQt5.QtWidgets import (QApplication, QFrame, QGridLayout, QHBoxLayout,
                             QLabel, QMainWindow, QPlainTextEdit, QPushButton,
                             QSlider, QSpinBox, QVBoxLayout, QWidget)

from engine import PokerEngine


class CardWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.card = None
        self.face_down = False
        back_path = os.path.join(
            os.path.dirname(__file__), "assets", "playing_card_back.png"
        )
        self.back_image = QPixmap(back_path)
        self.setFixedSize(60, 90)

    def setCard(self, card, face_down=False):
        self.card = card
        self.face_down = face_down
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        rect = event.rect()
        if self.card or self.face_down:
            painter.fillRect(rect, QColor("white"))
            painter.setPen(QColor("black"))
            painter.fillRect(rect, QColor('white'))
            painter.setPen(QColor('black'))
            painter.drawRect(rect)
        if self.face_down:
            painter.drawPixmap(rect, self.back_image)
        elif self.card:
            rank_map = {
                2: "2",
                3: "3",
                4: "4",
                5: "5",
                6: "6",
                7: "7",
                8: "8",
                9: "9",
                10: "10",
                11: "J",
                12: "Q",
                13: "K",
                14: "A",
            }
            suit_map = {0: "♣", 1: "♦", 2: "♥", 3: "♠"}
            r_text = rank_map[self.card[0]]
            s_text = suit_map[self.card[1]]
            text = r_text + s_text
            if self.card[1] in (1, 2):
                painter.setPen(QColor("red"))
            else:
                painter.setPen(QColor("black"))
            painter.setFont(QFont("Arial", 14, QFont.Bold))
            painter.drawText(rect, Qt.AlignCenter, text)


class SeatWidget(QWidget):
    def __init__(self, seat_id, parent=None):
        super().__init__(parent)
        self.seat_id = seat_id
        self._winner = False
        self._turn = False
        self.is_player = False
        layout = QVBoxLayout(self)
        self.info_label = QLabel(f"Seat {seat_id}")
        self.stack_label = QLabel("Stack: 0")
        self.bet_label = QLabel("Bet: 0")
        self.total_label = QLabel("Total: 0")
        cards_layout = QHBoxLayout()
        self.card1 = CardWidget()
        self.card2 = CardWidget()
        cards_layout.addWidget(self.card1)
        cards_layout.addWidget(self.card2)
        layout.addWidget(self.info_label, alignment=Qt.AlignCenter)
        layout.addLayout(cards_layout)
        layout.addWidget(self.stack_label, alignment=Qt.AlignCenter)
        layout.addWidget(self.bet_label, alignment=Qt.AlignCenter)
        layout.addWidget(self.total_label, alignment=Qt.AlignCenter)

    def _update_style(self) -> None:
        """Apply styling based on winner, turn, and player status."""
        parts = []
        if self._winner:
            parts.append("background-color: yellow")
        if self._turn:
            parts.append("border: 3px solid green; border-radius: 5px")
        elif self.is_player:
            parts.append("border: 2px solid blue")
        self.setStyleSheet("; ".join(parts))

    def setStack(self, stack):
        self.stack_label.setText(f"Stack: {stack}")

    def setBet(self, amount):
        self.bet_label.setText(f"Bet: {amount}")

    def setTotal(self, amount: int) -> None:
        self.total_label.setText(f"Total: {amount}")

    def setCards(self, cards, face_down=False):
        if cards:
            self.card1.setCard(cards[0], face_down)
            self.card2.setCard(cards[1], face_down)
        else:
            self.card1.setCard(None, face_down)
            self.card2.setCard(None, face_down)

    def highlight(self, state: bool) -> None:
        """Highlight this seat, typically when it wins a pot."""
        self._winner = state
        self._update_style()

    def set_turn(self, state: bool) -> None:
        self._turn = state
        self._update_style()

    def setPlayer(self, is_player: bool) -> None:
        """Mark this seat as belonging to the user."""
        self.is_player = is_player
        if is_player:
            self.info_label.setText(f"Seat {self.seat_id} (You)")
        else:
            self.info_label.setText(f"Seat {self.seat_id}")
        self._update_style()

class CommunityWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        self.cards = [CardWidget() for _ in range(5)]
        for cw in self.cards:
            layout.addWidget(cw)

    def setCards(self, cards):
        for i in range(5):
            if i < len(cards):
                self.cards[i].setCard(cards[i])
            else:
                self.cards[i].setCard(None)


class PotWidget(QWidget):
    """Widget displaying the pot amount as plain text."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.label = QLabel("0")
        layout.addWidget(self.label)

    def setAmount(self, amount: int) -> None:
        """Update the displayed pot amount."""
        self.label.setText(str(amount))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Poker Simulation")
        self.engine = PokerEngine(num_players=6)
        self.stage = 0
        self._auto_next = False
        central = QWidget()
        self.setCentralWidget(central)
        vbox = QVBoxLayout(central)

        table_frame = QFrame()
        table_frame.setStyleSheet("background-color: darkgreen; border-radius: 15px;")
        grid = QGridLayout(table_frame)
        grid.setSpacing(20)
        vbox.addWidget(table_frame)

        # create seats around the table
        self.seats = []
        positions = [(0, 0), (0, 1), (0, 2), (2, 0), (2, 1), (2, 2)]
        for i, pos in enumerate(positions):
            seat = SeatWidget(i)
            grid.addWidget(seat, pos[0], pos[1])
            self.seats.append(seat)

        # community cards and pot display at center
        center = QWidget()
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(0, 0, 0, 0)
        self.community = CommunityWidget()
        center_layout.addWidget(self.community, alignment=Qt.AlignCenter)
        self.pot_display = QLabel("Pot: 0")
        center_layout.addWidget(self.pot_display, alignment=Qt.AlignCenter)
        self.pot_widget = PotWidget()
        center_layout.addWidget(self.pot_widget, alignment=Qt.AlignCenter)
        grid.addWidget(center, 1, 1)

        # textual pot label below table
        self.pot_label = QLabel("Pot: 0")
        vbox.addWidget(self.pot_label, alignment=Qt.AlignCenter)

        # bot speed control
        ctrl_top = QHBoxLayout()
        ctrl_top.addWidget(QLabel("Bot Speed:"))
        self.bot_speed = QSlider(Qt.Horizontal)
        self.bot_speed.setRange(1, 5)
        ctrl_top.addWidget(self.bot_speed)
        vbox.addLayout(ctrl_top)

        # action controls
        action_layout = QHBoxLayout()
        self.fold_btn = QPushButton("Fold")
        self.fold_btn.clicked.connect(lambda: self.player_action("fold"))
        self.call_btn = QPushButton("Check")
        self.call_btn.clicked.connect(lambda: self.player_action("call"))
        self.bet_spin = QSpinBox()
        self.bet_spin.setRange(self.engine.bb_amt, 10000)
        self.bet_spin.setSingleStep(self.engine.bb_amt)
        self.bet_spin.setValue(self.engine.bb_amt)

        self.btn_3bb = QPushButton("3BB")
        self.btn_3bb.clicked.connect(
            lambda: self.set_bet_amount(self.engine.bb_amt * 3)
        )
        self.btn_half_pot = QPushButton("50% Pot")
        self.btn_half_pot.clicked.connect(
            lambda: self.set_bet_amount(self.engine.pot // 2)
        )
        self.btn_pot = QPushButton("Pot")
        self.btn_pot.clicked.connect(lambda: self.set_bet_amount(self.engine.pot))
        self.btn_max = QPushButton("Max")
        self.btn_max.clicked.connect(
            lambda: self.set_bet_amount(self.engine.stacks[self.player_seat])
        )

        self.bet_btn = QPushButton("Bet/Raise")
        self.bet_btn.clicked.connect(lambda: self.player_action("bet"))
        action_layout.addWidget(self.fold_btn)
        action_layout.addWidget(self.call_btn)
        action_layout.addWidget(self.bet_spin)
        action_layout.addWidget(self.btn_3bb)
        action_layout.addWidget(self.btn_half_pot)
        action_layout.addWidget(self.btn_pot)
        action_layout.addWidget(self.btn_max)
        action_layout.addWidget(self.bet_btn)
        vbox.addLayout(action_layout)

        # control button to start new hand
        self.button = QPushButton("Deal")
        self.button.clicked.connect(self.on_button)
        vbox.addWidget(self.button, alignment=Qt.AlignCenter)

        self.history_box = QPlainTextEdit()
        self.history_box.setReadOnly(True)
        self.history_box.setFixedHeight(150)
        vbox.addWidget(self.history_box)

        self.last_action_index = 0
        self.winners_displayed = False

        self._assign_random_seat()

    def _start_hand(self) -> None:
        """Deal a new hand and reset UI state."""
        self._auto_next = False
        self._assign_random_seat()
        holes = self.engine.new_hand()
        for i, seat in enumerate(self.seats):
            seat.highlight(False)
            seat.setStack(self.engine.stacks[i])
            seat.setBet(self.engine.contributions[i])
            seat.setTotal(self.engine.total_contrib[i])
            seat.setCards(holes.get(i), face_down=not seat.is_player)
            seat.set_turn(i == self.engine.turn)
        self.community.setCards([])
        self.pot_display.setText(f"Pot: {self.engine.pot}")
        self.pot_label.setText(f"Pot: {self.engine.pot}")
        self.stage = 1
        self.history_box.clear()
        self.last_action_index = 0
        self.winners_displayed = False
        self.update_display()
        self.bot_action()

    def _show_results(self) -> None:
        """Reveal hole cards, highlight winners, and schedule the next hand."""
        winners = (
            self.engine.hand_histories[-1]["winners"]
            if self.engine.hand_histories
            else []
        )
        win_map = {}
        for rec in winners:
            share = rec.get("share", rec.get("pot", 0) // max(1, len(rec.get("winners", []))))
            for w in rec.get("winners", []):
                win_map[w] = win_map.get(w, 0) + share
        win_set = set(win_map.keys())
        for i, seat in enumerate(self.seats):
            seat.setCards(self.engine.hole_cards.get(i))
            seat.highlight(i in win_set)
            seat.setTotal(self.engine.total_contrib[i])
            seat.set_turn(False)

        if win_set and not self.winners_displayed:
            for seat_num in sorted(win_map):
                amt = win_map[seat_num]
                self.history_box.appendPlainText(
                    f"Hand complete. Seat {seat_num} won {amt}"
                )
            self.winners_displayed = True
        self.button.setText("Deal")
        self.stage = 0
        if not self._auto_next:
            self._auto_next = True
            QTimer.singleShot(2000, self._start_hand)

    def _assign_random_seat(self) -> None:
        """Assign the user to a random seat and update labels."""
        self.player_seat = random.randrange(self.engine.num_players)
        for i, seat in enumerate(self.seats):
            seat.setPlayer(i == self.player_seat)

    def set_bet_amount(self, amount: int):
        """Set the bet spin box to ``amount`` clamped to the player's stack."""
        amount = max(0, min(int(amount), self.engine.stacks[self.player_seat]))
        self.bet_spin.setValue(amount)

    def player_action(self, action):
        if self.stage == 0:
            return
        if action == "fold":
            self.engine.player_action("fold")
        elif action == "call":
            if self.engine.contributions[self.player_seat] < self.engine.current_bet:
                self.engine.player_action("call")
            else:
                self.engine.player_action("check")
        elif action == "bet":
            amt = self.bet_spin.value()
            # A bet is only possible when no chips have been wagered in the
            # current betting round. Otherwise the action should be treated as
            # a raise against the existing bet.
            if self.engine.current_bet == 0:
                self.engine.player_action("bet", amt)
            else:
                self.engine.player_action("raise", amt)
        self.update_display()
        self.bot_action()

    def bot_action(self):
        if self.engine.stage == "complete" or self.engine.turn == self.player_seat:
            return
        if self.engine.contributions[self.engine.turn] < self.engine.current_bet:
            self.engine.player_action("call")
        else:
            self.engine.player_action("check")
        self.update_display()
        delay = 1000 // max(1, self.bot_speed.value())
        QTimer.singleShot(delay, self.bot_action)

    def update_display(self):
        for i, seat in enumerate(self.seats):
            seat.setStack(self.engine.stacks[i])
            seat.setBet(self.engine.contributions[i])
            seat.setTotal(self.engine.total_contrib[i])
            seat.set_turn(
                self.stage == 1
                and self.engine.stage != "complete"
                and i == self.engine.turn
            )
        self.community.setCards(self.engine.community)
        self.pot_display.setText(f"Pot: {self.engine.pot}")
        self.pot_widget.setAmount(self.engine.pot)
        self.pot_label.setText(f"Pot: {self.engine.pot}")
        self._update_action_controls()
        self.update_history()
        if (
            self.stage == 1
            and self.engine.stage == "complete"
            and not self._auto_next
        ):
            self._show_results()

    def _update_action_controls(self) -> None:
        """Enable or disable action buttons based on game state."""
        is_turn = (
            self.stage == 1
            and self.engine.stage != "complete"
            and self.engine.turn == self.player_seat
        )

        # Default disable everything
        for w in [
            self.fold_btn,
            self.call_btn,
            self.bet_spin,
            self.btn_3bb,
            self.btn_half_pot,
            self.btn_pot,
            self.btn_max,
            self.bet_btn,
        ]:
            w.setEnabled(is_turn)

        if not is_turn:
            return

        facing_bet = (
            self.engine.contributions[self.player_seat] < self.engine.current_bet
        )
        if facing_bet:
            to_call = self.engine.current_bet - self.engine.contributions[
                self.player_seat
            ]
            self.call_btn.setText(f"Call {to_call}")
            self.bet_btn.setText("Raise")
            can_raise = self.engine.stacks[self.player_seat] > to_call
            for w in [self.bet_spin, self.btn_3bb, self.btn_half_pot, self.btn_pot, self.btn_max, self.bet_btn]:
                w.setEnabled(can_raise)
        else:
            self.call_btn.setText("Check")
            self.bet_btn.setText("Bet")
            can_bet = self.engine.stacks[self.player_seat] > 0
            for w in [self.bet_spin, self.btn_3bb, self.btn_half_pot, self.btn_pot, self.btn_max, self.bet_btn]:
                w.setEnabled(can_bet)

    def update_history(self):
        hist = getattr(self.engine, "_current_history", None)
        if not hist:
            return
        actions = hist.get("actions", [])
        for action in actions[self.last_action_index :]:
            player = action.get("player")
            act = action.get("action")
            amt = action.get("amount", 0)
            if act == "blind":
                line = f"Seat {player} posted blind {amt}"
            elif act == "bet":
                line = f"Seat {player} bet {amt}"
            elif act == "raise":
                line = f"Seat {player} raised {amt}"
            elif act == "call":
                line = f"Seat {player} called {amt}"
            elif act == "check":
                line = f"Seat {player} checked"
            elif act == "fold":
                line = f"Seat {player} folded"
            else:
                line = f"Seat {player} {act} {amt}"
            self.history_box.appendPlainText(line)
        self.last_action_index = len(actions)

        if (
            self.engine.stage == "complete"
            and not self.winners_displayed
            and hist.get("winners")
        ):
            win_map = {}
            for rec in hist["winners"]:
                share = rec.get(
                    "share",
                    rec.get("pot", 0) // max(1, len(rec.get("winners", []))),
                )
                for w in rec.get("winners", []):
                    win_map[w] = win_map.get(w, 0) + share
            for seat_num in sorted(win_map):
                amt = win_map[seat_num]
                self.history_box.appendPlainText(
                    f"Hand complete. Seat {seat_num} won {amt}"
                )
            self.winners_displayed = True

    def on_button(self):
        if self.stage == 0:
            self._start_hand()
        elif self.stage == 1 and self.engine.stage == "complete":
            self._show_results()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
