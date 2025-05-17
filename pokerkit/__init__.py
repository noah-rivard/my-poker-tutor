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
