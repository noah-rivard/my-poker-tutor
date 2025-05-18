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
    QComboBox,
    QSpinBox,
    QSlider,
    QPlainTextEdit,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QColor, QFont
from engine import PokerEngine


class CardWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.card = None
        self.setFixedSize(60, 90)

    def setCard(self, card):
        self.card = card
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        rect = event.rect()
        painter.fillRect(rect, QColor('white'))
        painter.setPen(QColor('black'))
        painter.drawRect(rect)
        if self.card:
            rank_map = {2: '2', 3: '3', 4: '4', 5: '5', 6: '6',
                        7: '7', 8: '8', 9: '9', 10: '10',
                        11: 'J', 12: 'Q', 13: 'K', 14: 'A'}
            suit_map = {0: '♣', 1: '♦', 2: '♥', 3: '♠'}
            r_text = rank_map[self.card[0]]
            s_text = suit_map[self.card[1]]
            text = r_text + s_text
            if self.card[1] in (1, 2):
                painter.setPen(QColor('red'))
            else:
                painter.setPen(QColor('black'))
            painter.setFont(QFont('Arial', 14, QFont.Bold))
            painter.drawText(rect, Qt.AlignCenter, text)


class SeatWidget(QWidget):
    def __init__(self, seat_id, parent=None):
        super().__init__(parent)
        self.seat_id = seat_id
        self._winner = False
        self._turn = False

        self.is_player = False
        self.is_highlighted = False
        layout = QVBoxLayout(self)
        self.info_label = QLabel(f"Seat {seat_id}")
        self.stack_label = QLabel("Stack: 0")
        self.bet_label = QLabel("Bet: 0")
        cards_layout = QHBoxLayout()
        self.card1 = CardWidget()
        self.card2 = CardWidget()
        cards_layout.addWidget(self.card1)
        cards_layout.addWidget(self.card2)
        layout.addWidget(self.info_label, alignment=Qt.AlignCenter)
        layout.addLayout(cards_layout)
        layout.addWidget(self.stack_label, alignment=Qt.AlignCenter)
        layout.addWidget(self.bet_label, alignment=Qt.AlignCenter)

    def _apply_styles(self):
        parts = []
        if self._winner:
            parts.append("background-color: yellow")
        if self._turn:
            parts.append("border: 3px solid green; border-radius: 5px")
        self.setStyleSheet("; ".join(parts))

    def setStack(self, stack):
        self.stack_label.setText(f"Stack: {stack}")

    def setBet(self, amount):
        self.bet_label.setText(f"Bet: {amount}")

    def setCards(self, cards):
        if cards:
            self.card1.setCard(cards[0])
            self.card2.setCard(cards[1])
        else:
            self.card1.setCard(None)
            self.card2.setCard(None)

    def highlight(self, state):
        self._winner = state
        self._apply_styles()

    def set_turn(self, state: bool) -> None:
        self._turn = state
        self._apply_styles()
        
    def highlight(self, state: bool) -> None:
        """Highlight this seat, typically for winning a hand."""
        self.is_highlighted = state
        self._update_style()

    def setPlayer(self, is_player: bool) -> None:
        """Mark this seat as belonging to the user."""
        self.is_player = is_player
        if is_player:
            self.info_label.setText(f"Seat {self.seat_id} (You)")
        else:
            self.info_label.setText(f"Seat {self.seat_id}")
        self._update_style()

    def _update_style(self) -> None:
        """Apply style rules for highlight and player indication."""
        style = ""
        if self.is_highlighted:
            style += "background-color: yellow;"
        if self.is_player:
            style += "border: 2px solid blue;"
        self.setStyleSheet(style)


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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Poker Simulation")
        self.engine = PokerEngine(num_players=6)
        self.stage = 0
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
        positions = [(0, 0), (0, 1), (0, 2),
                     (2, 0), (2, 1), (2, 2)]
        for i, pos in enumerate(positions):
            seat = SeatWidget(i)
            grid.addWidget(seat, pos[0], pos[1])
            self.seats.append(seat)

        # community cards at center
        self.community = CommunityWidget()
        grid.addWidget(self.community, 1, 1)

        # pot display
        self.pot_label = QLabel("Pot: 0")
        vbox.addWidget(self.pot_label, alignment=Qt.AlignCenter)

        # seat/buy-in controls
        ctrl_top = QHBoxLayout()
        ctrl_top.addWidget(QLabel("Seat:"))
        self.seat_combo = QComboBox()
        self.seat_combo.addItems([str(i) for i in range(self.engine.num_players)])
        ctrl_top.addWidget(self.seat_combo)
        ctrl_top.addWidget(QLabel("Buy-in:"))
        self.buyin_spin = QSpinBox()
        self.buyin_spin.setRange(100, 10000)
        self.buyin_spin.setValue(self.engine.starting_stack)
        ctrl_top.addWidget(self.buyin_spin)
        self.join_button = QPushButton("Join")
        self.join_button.clicked.connect(self.join_game)
        ctrl_top.addWidget(self.join_button)
        ctrl_top.addWidget(QLabel("Rebuy:"))
        self.rebuy_spin = QSpinBox()
        self.rebuy_spin.setRange(100, 10000)
        ctrl_top.addWidget(self.rebuy_spin)
        self.rebuy_button = QPushButton("Rebuy")
        self.rebuy_button.clicked.connect(self.rebuy)
        ctrl_top.addWidget(self.rebuy_button)
        ctrl_top.addWidget(QLabel("Bot Speed:"))
        self.bot_speed = QSlider(Qt.Horizontal)
        self.bot_speed.setRange(1, 5)
        ctrl_top.addWidget(self.bot_speed)
        vbox.addLayout(ctrl_top)

        # action controls
        action_layout = QHBoxLayout()
        self.fold_btn = QPushButton("Fold")
        self.fold_btn.clicked.connect(lambda: self.player_action("fold"))
        self.call_btn = QPushButton("Call/Check")
        self.call_btn.clicked.connect(lambda: self.player_action("call"))
        self.bet_spin = QSpinBox()
        self.bet_spin.setRange(1, 10000)
        self.bet_spin.setSingleStep(self.engine.bb_amt)

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

        self.player_seat = 0

    def join_game(self):
        self.player_seat = int(self.seat_combo.currentText())
        self.engine.stacks[self.player_seat] = self.buyin_spin.value()
        for i, seat in enumerate(self.seats):
            seat.setPlayer(i == self.player_seat)
        self.seat_combo.setDisabled(True)
        self.join_button.setDisabled(True)
        self.update_display()

    def rebuy(self):
        self.engine.add_chips(self.player_seat, self.rebuy_spin.value())
        self.update_display()

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
            if self.engine.current_bet == self.engine.contributions[self.player_seat]:
                self.engine.player_action("bet", amt)
            else:
                self.engine.player_action("raise", amt)
        self.bot_action()
        self.update_display()

    def bot_action(self):
        while self.engine.stage != "complete" and self.engine.turn != self.player_seat:
            if self.engine.contributions[self.engine.turn] < self.engine.current_bet:
                self.engine.player_action("call")
            else:
                self.engine.player_action("check")

    def update_display(self):
        for i, seat in enumerate(self.seats):
            seat.setStack(self.engine.stacks[i])
            seat.setBet(self.engine.contributions[i])
            seat.set_turn(
                self.stage == 1
                and self.engine.stage != "complete"
                and i == self.engine.turn
            )
        self.community.setCards(self.engine.community)
        self.pot_label.setText(f"Pot: {self.engine.pot}")
        self.update_history()

    def update_history(self):
        hist = getattr(self.engine, "_current_history", None)
        if not hist:
            return
        actions = hist.get("actions", [])
        for action in actions[self.last_action_index:]:
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

    def on_button(self):
        if self.stage == 0:
            holes = self.engine.new_hand()
            for i, seat in enumerate(self.seats):
                seat.highlight(False)
                seat.setStack(self.engine.stacks[i])
                seat.setBet(self.engine.contributions[i])
                seat.setCards(holes.get(i))
                seat.set_turn(i == self.engine.turn)
            self.community.setCards([])
            self.pot_label.setText(f"Pot: {self.engine.pot}")
            self.stage = 1
            self.history_box.clear()
            self.last_action_index = 0
            self.bot_action()
            self.update_display()
        elif self.stage == 1 and self.engine.stage == "complete":
            winners = self.engine.hand_histories[-1]["winners"] if self.engine.hand_histories else []
            win_set = set()
            for rec in winners:
                win_set.update(rec.get("winners", []))
            for i, seat in enumerate(self.seats):
                seat.highlight(i in win_set)
            if win_set:
                winner_seats = ", ".join(str(s) for s in sorted(win_set))
                self.history_box.appendPlainText(
                    f"Hand complete. Winners: {winner_seats}"
                )

                seat.highlight(i in winners)
                seat.set_turn(False)
            self.button.setText("Deal")
            self.stage = 0


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
