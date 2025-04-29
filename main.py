import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QGridLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame
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
        layout = QVBoxLayout(self)
        self.info_label = QLabel(f"Seat {seat_id}")
        self.stack_label = QLabel("Stack: 0")
        cards_layout = QHBoxLayout()
        self.card1 = CardWidget()
        self.card2 = CardWidget()
        cards_layout.addWidget(self.card1)
        cards_layout.addWidget(self.card2)
        layout.addWidget(self.info_label, alignment=Qt.AlignCenter)
        layout.addLayout(cards_layout)
        layout.addWidget(self.stack_label, alignment=Qt.AlignCenter)

    def setStack(self, stack):
        self.stack_label.setText(f"Stack: {stack}")

    def setCards(self, cards):
        if cards:
            self.card1.setCard(cards[0])
            self.card2.setCard(cards[1])
        else:
            self.card1.setCard(None)
            self.card2.setCard(None)

    def highlight(self, state):
        if state:
            self.setStyleSheet("background-color: yellow")
        else:
            self.setStyleSheet("")


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
        grid = QGridLayout()
        grid.setSpacing(20)
        vbox.addLayout(grid)

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

        # control button
        self.button = QPushButton("Deal")
        self.button.clicked.connect(self.on_button)
        vbox.addWidget(self.button, alignment=Qt.AlignCenter)

    def on_button(self):
        if self.stage == 0:
            holes = self.engine.new_hand()
            # update seats
            for i, seat in enumerate(self.seats):
                seat.highlight(False)
                seat.setStack(self.engine.stacks[i])
                seat.setCards(holes.get(i))
            self.community.setCards([])
            self.button.setText("Flop")
            self.stage = 1
        elif self.stage == 1:
            flop = self.engine.deal_flop()
            self.community.setCards(flop)
            self.button.setText("Turn")
            self.stage = 2
        elif self.stage == 2:
            turn = self.engine.deal_turn()
            self.community.setCards(turn)
            self.button.setText("River")
            self.stage = 3
        elif self.stage == 3:
            river = self.engine.deal_river()
            self.community.setCards(river)
            self.button.setText("Showdown")
            self.stage = 4
        elif self.stage == 4:
            winners = self.engine.showdown()
            for i, seat in enumerate(self.seats):
                seat.highlight(i in winners)
                seat.setStack(self.engine.stacks[i])
            self.button.setText("Deal")
            self.stage = 0


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())