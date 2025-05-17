import random

class StandardHighHand:
    def __init__(self, strength):
        self.strength = strength

    def __gt__(self, other):
        return self.strength > other.strength

    def __eq__(self, other):
        return self.strength == other.strength

    @classmethod
    def from_game_or_none(cls, hole_str, board_str):
        return cls(random.random())
