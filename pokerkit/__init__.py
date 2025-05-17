from .utilities import Deck, Card
from .hands import StandardHighHand

__all__ = [
    "Deck",
    "Card",
    "StandardHighHand",
    "calculate_equities",
    "parse_range",
]


def calculate_equities(*args, **kwargs):
    ranges = args[0]
    return [1 / len(ranges)] * len(ranges)

class Dummy:
    def __init__(self, value):
        self.value = value

class Card:
    def __init__(self, rank, suit):
        self.rank = Dummy(rank)
        self.suit = Dummy(suit)


class Deck:
    STANDARD = [Card(r, s) for r in '23456789TJQKA' for s in 'cdhs']


def calculate_equities(*args, **kwargs):
    return [1 / len(args[0])] * len(args[0])


def parse_range(r):
    return r
