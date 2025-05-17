from dataclasses import dataclass


@dataclass(frozen=True)
class _Value:
    value: str


@dataclass(frozen=True)
class Card:
    rank: _Value
    suit: _Value


class Deck:
    STANDARD = [Card(_Value(r), _Value(s)) for r in "23456789TJQKA" for s in "cdhs"]

from . import Deck, Card
