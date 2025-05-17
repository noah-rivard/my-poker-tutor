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


def parse_range(r):
    return r
