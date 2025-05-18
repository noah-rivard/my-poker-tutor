"""
engine.py

Poker game engine for Texas Hold'em using pokerkit.
"""

import json
import random

from pokerkit.hands import StandardHighHand
from pokerkit.utilities import Card as PKCard
from pokerkit.utilities import Deck


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

        # betting state
        self.stage = None  # 'preflop', 'flop', 'turn', 'river', 'complete'
        self.active = [True] * num_players
        self.contributions = [0] * num_players
        self.total_contrib = [0] * num_players
        self.all_in = [False] * num_players
        self.current_bet = 0
        self.turn = 0
        self.last_raiser = None

        # hand histories
        self.hand_histories = []
        self._current_history = None

    def new_hand(self):
        """Start a new hand and reset all betting state."""
        self.button = (self.button + 1) % self.num_players
        self.sb = (self.button + 1) % self.num_players
        self.bb = (self.sb + 1) % self.num_players

        # reset state
        self.active = [True] * self.num_players
        self.contributions = [0] * self.num_players
        self.total_contrib = [0] * self.num_players
        self.all_in = [False] * self.num_players
        self.current_bet = self.bb_amt
        self.stage = "preflop"
        self.last_raiser = self.bb

        # set up history for this hand
        self._current_history = {
            "button": self.button,
            "sb": self.sb,
            "bb": self.bb,
            "actions": [],
            "hole_cards": {},
            "community": [],
            "starting_stacks": self.stacks.copy(),
        }

        # post blinds
        self.stacks[self.sb] -= self.sb_amt
        self.stacks[self.bb] -= self.bb_amt
        self.contributions[self.sb] = self.sb_amt
        self.contributions[self.bb] = self.bb_amt
        self.total_contrib[self.sb] = self.sb_amt
        self.total_contrib[self.bb] = self.bb_amt
        self.pot = self.sb_amt + self.bb_amt
        if self.stacks[self.sb] == 0:
            self.all_in[self.sb] = True
        if self.stacks[self.bb] == 0:
            self.all_in[self.bb] = True

        self._current_history["actions"].append(
            {
                "player": self.sb,
                "action": "blind",
                "amount": self.sb_amt,
                "stage": "preflop",
            }
        )
        self._current_history["actions"].append(
            {
                "player": self.bb,
                "action": "blind",
                "amount": self.bb_amt,
                "stage": "preflop",
            }
        )

        # shuffle and deal
        self.deck = list(Deck.STANDARD)
        random.shuffle(self.deck)
        self.hole_cards = {}
        for i in range(self.num_players):
            c1 = self.deck.pop()
            c2 = self.deck.pop()
            cards = [self._card_to_tuple(c1), self._card_to_tuple(c2)]
            self.hole_cards[i] = cards
            self._current_history["hole_cards"][i] = cards
        self.community = []

        # first player to act preflop
        self.turn = (self.bb + 1) % self.num_players
        return self.hole_cards

    # ------------------------------------------------------------------
    # Betting logic
    # ------------------------------------------------------------------
    def player_action(self, action, amount=0):
        """Apply an action for the current player.

        Parameters
        ----------
        action : str
            One of 'fold', 'check', 'call', 'bet', or 'raise'.
        amount : int, optional
            Additional chips for bet/raise actions.
        """
        player = self.turn

        if not self.active[player]:
            raise ValueError("Player already folded")
        if self.all_in[player]:
            raise ValueError("Player is all-in and cannot act")

        if action == "fold":
            self.active[player] = False
            event_amount = 0

        elif action == "check":
            if self.contributions[player] != self.current_bet:
                raise ValueError("Cannot check when facing a bet")
            event_amount = 0

        elif action == "call":
            to_call = self.current_bet - self.contributions[player]
            actual = min(to_call, self.stacks[player])
            self.stacks[player] -= actual
            self.contributions[player] += actual
            self.total_contrib[player] += actual
            self.pot += actual
            event_amount = actual
            if self.stacks[player] == 0:
                self.all_in[player] = True

        elif action == "bet":
            if self.current_bet != self.contributions[player]:
                raise ValueError("Cannot bet when facing a bet")
            if amount <= 0:
                raise ValueError("Bet amount must be positive")
            if amount > self.stacks[player]:
                amount = self.stacks[player]
            self.current_bet = self.contributions[player] + amount
            self.stacks[player] -= amount
            self.contributions[player] += amount
            self.total_contrib[player] += amount
            self.pot += amount
            self.last_raiser = player
            event_amount = amount
            if self.stacks[player] == 0:
                self.all_in[player] = True

        elif action == "raise":
            if amount <= 0:
                raise ValueError("Raise amount must be positive")
            to_call = self.current_bet - self.contributions[player]
            raise_total = to_call + amount
            actual = min(raise_total, self.stacks[player])
            self.stacks[player] -= actual
            self.contributions[player] += actual
            self.total_contrib[player] += actual
            self.pot += actual
            self.current_bet = self.contributions[player]
            self.last_raiser = player
            event_amount = actual
            if self.stacks[player] == 0:
                self.all_in[player] = True
        else:
            raise ValueError(f"Unknown action: {action}")

        if self._current_history is not None:
            self._current_history["actions"].append(
                {
                    "player": player,
                    "action": action,
                    "amount": event_amount,
                    "stage": self.stage,
                }
            )

        self._next_player()

    def _next_player(self):
        """Advance to the next active player and progress rounds."""
        if sum(self.active) == 1:
            winner = next(i for i, a in enumerate(self.active) if a)
            self.stacks[winner] += self.pot
            if self._current_history is not None:
                winners_record = [{"pot": self.pot, "winners": [winner], "share": self.pot}]
                self._current_history["winners"] = winners_record
                self._current_history["final_stacks"] = self.stacks.copy()
                self._current_history["community"] = self.community.copy()
                self.hand_histories.append(self._current_history)
                self._current_history = None
            self.pot = 0
            self.stage = "complete"
            return

        start = self.turn
        found = False
        for _ in range(self.num_players):
            self.turn = (self.turn + 1) % self.num_players
            if self.active[self.turn] and not self.all_in[self.turn]:
                found = True
                break
        if not found:
            while self.stage != "river":
                self._end_betting_round()
            self.stage = "complete"
            self.showdown()
            return

        # determine if betting round is complete
        round_complete = self.turn == self.last_raiser and all(
            not a or self.contributions[i] == self.current_bet or self.all_in[i]
            for i, a in enumerate(self.active)
        )

        if round_complete:
            self._end_betting_round()

    def _end_betting_round(self):
        """Move to the next stage of the hand."""
        self.contributions = [0] * self.num_players
        self.current_bet = 0

        if self.stage == "preflop":
            self.deal_flop()
            self.stage = "flop"

            if self._current_history is not None:
                self._current_history["community"] = self.community.copy()
        elif self.stage == "flop":
            self.deal_turn()
            self.stage = "turn"
            if self._current_history is not None:
                self._current_history["community"] = self.community.copy()
        elif self.stage == "turn":
            self.deal_river()
            self.stage = "river"
            if self._current_history is not None:
                self._current_history["community"] = self.community.copy()

        elif self.stage == "river":
            self.stage = "complete"
            self.showdown()
            return

        # next round first player is seat left of button
        self.turn = (self.button + 1) % self.num_players
        self.last_raiser = self.turn

    def _compute_side_pots(self):
        """Return list of side pots based on total contributions."""
        contribs = [(amt, i) for i, amt in enumerate(self.total_contrib) if amt > 0]
        contribs.sort()
        pots = []
        prev = 0
        remaining = {i for _, i in contribs}
        for amt, player in contribs:
            if amt > prev:
                participants = [p for p in remaining]
                pots.append(
                    {
                        "amount": (amt - prev) * len(participants),
                        "players": participants.copy(),
                    }
                )
                prev = amt
            remaining.remove(player)
        return pots

    def deal_flop(self):
        # burn
        self.deck.pop()
        # deal 3 board cards
        flop = []
        for _ in range(3):
            flop.append(self._card_to_tuple(self.deck.pop()))
        self.community = flop
        if self._current_history is not None:
            self._current_history["community"] = self.community.copy()
        return self.community

    def deal_turn(self):
        # burn
        self.deck.pop()
        # deal 1 board card
        self.community.append(self._card_to_tuple(self.deck.pop()))
        if self._current_history is not None:
            self._current_history["community"] = self.community.copy()
        return self.community

    def deal_river(self):
        # burn
        self.deck.pop()
        # deal 1 board card
        self.community.append(self._card_to_tuple(self.deck.pop()))
        if self._current_history is not None:
            self._current_history["community"] = self.community.copy()
        return self.community

    def showdown(self):
        board_str = "".join(self._tuple_to_str(c) for c in self.community)
        hands = {}
        for i in range(self.num_players):
            if not self.active[i] and not self.all_in[i]:
                continue
            hole = self.hole_cards[i]
            hole_str = "".join(self._tuple_to_str(c) for c in hole)
            hand = StandardHighHand.from_game_or_none(hole_str, board_str)
            if hand is not None:
                hands[i] = hand

        side_pots = self._compute_side_pots()
        winners_record = []
        for pot in side_pots:
            eligible = [p for p in pot["players"] if p in hands]
            if not eligible:
                continue
            best_hand = None
            winners = []
            for p in eligible:
                h = hands[p]
                if best_hand is None or h > best_hand:
                    best_hand = h
                    winners = [p]
                elif h == best_hand:
                    winners.append(p)
            share = pot["amount"] // len(winners)
            for w in winners:
                self.stacks[w] += share
            winners_record.append({
                "pot": pot["amount"],
                "winners": winners,
                "share": share,
            })

        if self._current_history is not None:
            self._current_history["winners"] = winners_record
            self._current_history["final_stacks"] = self.stacks.copy()
            self._current_history["community"] = self.community.copy()
            self.hand_histories.append(self._current_history)
            self._current_history = None
        self.pot = 0
        return winners_record

    def _card_to_tuple(self, card: PKCard):
        # convert pokerkit Card to (rank_int, suit_int)
        rank_map = {
            "2": 2,
            "3": 3,
            "4": 4,
            "5": 5,
            "6": 6,
            "7": 7,
            "8": 8,
            "9": 9,
            "T": 10,
            "J": 11,
            "Q": 12,
            "K": 13,
            "A": 14,
        }
        suit_map = {"c": 0, "d": 1, "h": 2, "s": 3}
        rank_char = card.rank.value
        suit_char = card.suit.value
        return (rank_map[rank_char], suit_map[suit_char])

    def _tuple_to_str(self, card_tuple):
        # convert (rank_int, suit_int) to card string like 'As'
        rank_map = {
            2: "2",
            3: "3",
            4: "4",
            5: "5",
            6: "6",
            7: "7",
            8: "8",
            9: "9",
            10: "T",
            11: "J",
            12: "Q",
            13: "K",
            14: "A",
        }
        suit_map = {0: "c", 1: "d", 2: "h", 3: "s"}
        return rank_map[card_tuple[0]] + suit_map[card_tuple[1]]

    def save_histories(self, path):
        """Persist recorded hand histories to a JSON file."""
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(self.hand_histories, fh)

    def add_chips(self, player: int, amount: int) -> None:
        """Add chips to a player's stack."""
        self.stacks[player] += amount
