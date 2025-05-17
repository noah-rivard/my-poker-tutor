class StandardHighHand:
    def __init__(self, value=0):
        self.value = value

    @staticmethod
    def from_game_or_none(hole_str, board_str):
        # very naive evaluation based on string lengths
        return StandardHighHand(len(hole_str) + len(board_str))

    def __gt__(self, other):
        return self.value > getattr(other, "value", -1)

    def __eq__(self, other):
        return self.value == getattr(other, "value", -1)
