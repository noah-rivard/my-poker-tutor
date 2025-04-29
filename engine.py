"""
engine.py

Poker game engine for Texas Hold'em using pokerkit.
"""
import random
from pokerkit.utilities import Deck, Card as PKCard
from pokerkit.hands import StandardHighHand

class PokerEngine:
    def __init__(self, num_players=6, starting_stack=1000, sb_amt=10, bb_amt=20):
        self.num_players = num_players
        self.starting_stack = starting_stack
        self.sb_amt = sb_amt
        self.bb_amt = bb_amt
        self.stacks = [starting_stack] * num_players
        self.button = -1
        self.deck = []
        self.hole_cards = {}
        self.community = []
        self.pot = 0

    def new_hand(self):
        self.button = (self.button + 1) % self.num_players
        self.sb = (self.button + 1) % self.num_players
        self.bb = (self.sb + 1) % self.num_players
        # post blinds
        self.stacks[self.sb] -= self.sb_amt
        self.stacks[self.bb] -= self.bb_amt
        self.pot = self.sb_amt + self.bb_amt
        # shuffle deck
        self.deck = list(Deck.STANDARD)
        random.shuffle(self.deck)
        # deal hole cards
        self.hole_cards = {}
        for i in range(self.num_players):
            c1 = self.deck.pop()
            c2 = self.deck.pop()
            self.hole_cards[i] = [self._card_to_tuple(c1), self._card_to_tuple(c2)]
        self.community = []
        return self.hole_cards

    def deal_flop(self):
        # burn
        self.deck.pop()
        # deal 3 board cards
        flop = []
        for _ in range(3):
            flop.append(self._card_to_tuple(self.deck.pop()))
        self.community = flop
        return self.community

    def deal_turn(self):
        # burn
        self.deck.pop()
        # deal 1 board card
        self.community.append(self._card_to_tuple(self.deck.pop()))
        return self.community

    def deal_river(self):
        # burn
        self.deck.pop()
        # deal 1 board card
        self.community.append(self._card_to_tuple(self.deck.pop()))
        return self.community

    def showdown(self):
        best_hand = None
        winners = []
        # build board and hole card strings
        board_str = ''.join(self._tuple_to_str(c) for c in self.community)
        for i in range(self.num_players):
            hole = self.hole_cards[i]
            hole_str = ''.join(self._tuple_to_str(c) for c in hole)
            hand = StandardHighHand.from_game_or_none(hole_str, board_str)
            if hand is None:
                continue
            if best_hand is None or hand > best_hand:
                best_hand = hand
                winners = [i]
            elif hand == best_hand:
                winners.append(i)
        # distribute pot evenly
        share = self.pot // len(winners) if winners else 0
        for i in winners:
            self.stacks[i] += share
        return winners

    def _card_to_tuple(self, card: PKCard):
        # convert pokerkit Card to (rank_int, suit_int)
        rank_map = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6,
                    '7': 7, '8': 8, '9': 9, 'T': 10, 'J': 11,
                    'Q': 12, 'K': 13, 'A': 14}
        suit_map = {'c': 0, 'd': 1, 'h': 2, 's': 3}
        rank_char = card.rank.value
        suit_char = card.suit.value
        return (rank_map[rank_char], suit_map[suit_char])
    
    def _tuple_to_str(self, card_tuple):
        # convert (rank_int, suit_int) to card string like 'As'
        rank_map = {2: '2', 3: '3', 4: '4', 5: '5', 6: '6',
                    7: '7', 8: '8', 9: '9', 10: 'T', 11: 'J',
                    12: 'Q', 13: 'K', 14: 'A'}
        suit_map = {0: 'c', 1: 'd', 2: 'h', 3: 's'}
        return rank_map[card_tuple[0]] + suit_map[card_tuple[1]]