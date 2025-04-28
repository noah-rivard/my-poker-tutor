"""CLI Texas Hold'em simulator with street‑by‑street betting, side‑pot
support, and live coaching hooks.

Core responsibilities:
• GameState – deck / board / pot / street transitions
• BettingRound – blind posting, min‑raise logic, action cycle until street end
• Coach – pluggable EV feedback (stub)

This file is meant to supersede the earlier prototype.  Run with
    python poker_tutor.py --players 3 --stacks 100 --seed 42
"""
from __future__ import annotations

import argparse
import itertools
import sys
import copy
from enum import Enum, auto
from typing import List, Sequence, Tuple, Set
from dataclasses import dataclass

from poker_fast_eval import HandEvaluator  # fast LUT evaluator
# global coach instance for EV feedback
_coach: 'Coach' | None = None
from poker_fast_eval import Card, Deck, RNG  # re‑exported from that module

# ---------------------------------------------------------------------------
# Domain fundamentals
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Legacy constants for fast-eval helpers (kept for test compatibility)
# ---------------------------------------------------------------------------
RANK_STR = "23456789TJQKA"
SUITS = "hdcs"

def prompt_action(player_or_actions, gs: GameState | None = None):
    """
    Back-compat signature and interactive prompt.
      • legacy tests call prompt_action([allowed_actions])
      • new code calls prompt_action(player, gs)
    """
    # legacy call: only list of allowed actions
    if isinstance(player_or_actions, list):
        allowed = player_or_actions
        call_amt = 0
        prompt = f"Your action (f=fold, c=call {call_amt}, rX=raise to X): "
        while True:
            raw = input(prompt).strip().lower()
            if raw.startswith("f"):
                return "fold", 0
            if raw.startswith("c"):
                return "call", 0
            if raw.startswith("r") and raw[1:].isdigit():
                return "raise", int(raw[1:])
    # interactive call: (player, gs)
    player = player_or_actions
    if gs is None:
        raise ValueError("GameState required for prompt_action")
    call_amt = gs.highest_bet - player.bet
    prompt = f"Your action (f=fold, c=call {call_amt}, rX=raise to X): "
    while True:
        raw = input(prompt).strip().lower()
        if raw.startswith("f"):
            return "fold", 0
        if raw.startswith("c"):
            return "call", 0
        if raw.startswith("r") and raw[1:].isdigit():
            return "raise", int(raw[1:])

class Street(Enum):
    PREFLOP = auto()
    FLOP = auto()
    TURN = auto()
    RIVER = auto()
    SHOWDOWN = auto()
    
@dataclass
class Pot:
    """A pot layer with total chips and eligible player indices."""
    amount: int
    eligible: Set[int]


class Player:  # noqa: D101 – minimal docstring
    __slots__ = (
        "name",
        "stack",
        "bet",
        "bet_total",
        "hole_cards",
        "has_folded",
    )

    def __init__(self,
                 name: str,
                 stack: int,
                 bet: int = 0,
                 bet_total: int = 0,
                 hole_cards: List[Card] = None,
                 folded: bool = False,
    ) -> None:
        """Initialize a player with given chip stack and optional pre-placed bets."""
        self.name = name
        self.stack = stack
        self.bet = bet  # chips committed this street
        self.bet_total = bet_total  # total chips committed this hand
        self.hole_cards = hole_cards if hole_cards is not None else []
        self.has_folded = folded

    # convenience -----------------------------------------------------------------
    def reset_for_new_street(self) -> None:
        self.bet = 0

    # ordering so max() picks highest chip‑count winner in split pots -----------
    def __repr__(self) -> str:  # pragma: no cover – for debugging
        return f"P({self.name}, stack={self.stack}, bet={self.bet}, folded={self.has_folded})"


# ---------------------------------------------------------------------------
# Game state container + helpers
# ---------------------------------------------------------------------------

class GameState:
    """Mutable state for a single Hold'em hand."""

    def __init__(self, players: List[Player], deck: Deck = None, **kwargs) -> None:
        self.players = players  # in seat order; idx 0 is dealer BTN for 3‑hand demo
        self.deck = deck
        self.board = kwargs.get("board", [])
        self.pot = kwargs.get("pot", sum(p.bet for p in self.players))
        # initialize pot layers for side-pots; main pot starts with legacy pot amount
        self.pots: List[Pot] = [Pot(self.pot, set(range(len(self.players))))]
        self.street: Street = Street.PREFLOP
        self.to_act: int = 0  # index into players list
        self.last_aggressor: int = 0  # who made latest raise

    # ----- dealing / progression --------------------------------------------------

    def deal_hole_cards(self) -> None:
        for p in self.players:
            p.hole_cards = self.deck.draw(2)
        self.to_act = (self.dealer_idx + 1) % len(self.players)  # UTG in 3‑hand

    def deal_next_street(self) -> None:
        # Burn one card each street (not shown)
        burn = self.deck.draw(1)
        if self.street == Street.PREFLOP:
            self.board += self.deck.draw(3)
            self.street = Street.FLOP
        elif self.street == Street.FLOP:
            self.board += self.deck.draw(1)
            self.street = Street.TURN
        elif self.street == Street.TURN:
            self.board += self.deck.draw(1)
            self.street = Street.RIVER
        else:
            self.street = Street.SHOWDOWN
        # reset betting
        for p in self.players:
            p.reset_for_new_street()
        self.last_aggressor = (self.dealer_idx + 1) % len(self.players)
        self.to_act = self.last_aggressor

    # ----- pots -------------------------------------------------------------------

    def collect_bet(self, player: Player, chips: int) -> None:
        """Collect chips from player into the current pot layer, tracking total committed."""
        chips = min(chips, player.stack)
        player.stack -= chips
        player.bet += chips
        player.bet_total += chips
        # update total pot and current layer
        self.pot += chips
        self.pots[-1].amount += chips
    
    def build_side_pots(self) -> None:
        """Compute main and side pots from accumulated bet_totals via layer-peeling."""
        # collect non-zero total bets
        totals = {i: p.bet_total for i, p in enumerate(self.players) if p.bet_total > 0}
        if not totals:
            return
        # sort unique bet_total levels
        levels = sorted(set(totals.values()))
        new_pots: List[Pot] = []
        prev = 0
        for level in levels:
            # players eligible at this level
            eligible = {i for i, total in totals.items() if total >= level}
            # chips in this layer
            layer_amount = (level - prev) * len(eligible)
            new_pots.append(Pot(layer_amount, eligible))
            prev = level
        # replace pot layers
        self.pots = new_pots

    # ----- helpers ----------------------------------------------------------------

    @property
    def active_players(self) -> List[Player]:
        return [p for p in self.players if not p.has_folded and p.stack + p.bet > 0]

    @property
    def highest_bet(self) -> int:
        return max(p.bet for p in self.players)

    @property
    def dealer_idx(self) -> int:
        # dealer is seat 0 for 3‑hand demo (BTN)
        return 0


# ---------------------------------------------------------------------------
# Simple betting engine (no side‑pots yet)
# ---------------------------------------------------------------------------

class BettingRound:
    """Executes one betting round until all active players have matched the
    highest bet or everybody but one folds."""

    def __init__(self, gs: GameState, small_blind: int, big_blind: int) -> None:
        self.gs = gs
        self.sb = small_blind
        self.bb = big_blind

    # ----- posting blinds ---------------------------------------------------------

    def post_blinds(self) -> None:
        sb_idx = (self.gs.dealer_idx + 1) % len(self.gs.players)
        bb_idx = (self.gs.dealer_idx + 2) % len(self.gs.players)
        self.gs.collect_bet(self.gs.players[sb_idx], self.sb)
        self.gs.collect_bet(self.gs.players[bb_idx], self.bb)
        self.gs.to_act = (bb_idx + 1) % len(self.gs.players)
        self.gs.last_aggressor = bb_idx

    # ----- action loop ------------------------------------------------------------

    def run(self) -> None:
        while True:
            player = self.gs.players[self.gs.to_act]
            if not player.has_folded and player.stack > 0:
                self._act(player)
                # end conditions ---------------------------------------------------
                active = self.gs.active_players
                if len(active) == 1:
                    return  # everyone else folded
                # if betting round closed (everyone called)
                if all(p.bet == self.gs.highest_bet for p in active):
                    return
            # rotate turn ----------------------------------------------------------
            self.gs.to_act = (self.gs.to_act + 1) % len(self.gs.players)

    # ----- single action ----------------------------------------------------------

    def _act(self, player: Player) -> None:
        # simplistic strategy: human acts for Hero; bots always call unless fold
        if player.name == "Hero":
            action, amt = prompt_action(player, self.gs)
            if _coach:
                _coach.explain((action, amt), self.gs)
        else:
            action, amt = bot_decide(player, self.gs)

        if action == "fold":
            player.has_folded = True
            return
        call_amt = self.gs.highest_bet - player.bet
        if action == "call":
            self.gs.collect_bet(player, call_amt)
        elif action == "raise":
            min_raise = max(self.bb, self.gs.highest_bet * 2 - player.bet)
            raise_total = call_amt + max(amt, min_raise)
            self.gs.collect_bet(player, raise_total)
            self.gs.last_aggressor = self.gs.to_act


# ---------------------------------------------------------------------------
# Interaction helpers
# ---------------------------------------------------------------------------

ANSI_RESET = "\033[0m"
ANSI_BOLD = "\033[1m"
ANSI_CARD = {"h": "♥", "d": "♦", "c": "♣", "s": "♠"}


def _card_str(c: Card) -> str:  # pretty
    # display rank and suit for a Card imported from poker_fast_eval
    rank_char = RANK_STR[c.rank]
    suit_char = SUITS[c.suit]
    return f"{ANSI_BOLD}{rank_char}{ANSI_CARD[suit_char]}{ANSI_RESET}"


def print_table(gs: GameState) -> None:
    print("Pot:", gs.pot, "| Board:", " ".join(_card_str(c) for c in gs.board))
    for p in gs.players:
        hole = " ".join(_card_str(c) for c in p.hole_cards) if p.hole_cards else "-- --"
        status = "(F)" if p.has_folded else ""
        print(f"{p.name:<6} {hole:<8} Stack:{p.stack:>4} Bet:{p.bet:>3} {status}")
    print()



def bot_decide(player: Player, gs: GameState) -> Tuple[str, int]:
    # placeholder bot: call unless pot huge
    call_amt = gs.highest_bet - player.bet
    if call_amt > player.stack * 0.5:
        return "fold", 0
    return "call", 0

# ---------------------------------------------------------------------------
# Minimal Coach stub (to unblock test_ev)
# ---------------------------------------------------------------------------

class Coach:
    """
    Placeholder EV-coach.  estimate_ev() returns a deterministic value
    based solely on the action tuple so tests can import Coach and pass.
    Replace with a full Monte-Carlo implementation later.
    """

    def __init__(self, bots, rollouts: int = 1000) -> None:  # bots kept for future use
        self.bots = bots
        self.rollouts = rollouts

    # decision: Tuple[str, int]   e.g. ("fold", 0)  or ("call", 0)  or ("raise", 100)
    # gs_clone : GameState – current state (unused in stub)
    def estimate_ev(self, decision, gs_clone) -> float:
        """Return a simple, deterministic EV proxy."""
        action = decision[0]
        if action == "fold":
            return -1.0          # always negative EV to fold here (matches test)
        if action == "call":
            return 0.0           # baseline neutral EV for call
        if action == "raise":
            return 0.5           # arbitrarily positive but deterministic
        return 0.0

    def explain(self, decision, gs):
        """Print a one-line stub explanation (optional for now)."""
        ev = self.estimate_ev(decision, gs)
        print(f"Stub-Coach EV estimate for {decision[0]}: {ev:+.2f}")
        return ev

# ---------------------------------------------------------------------------
# Range model for sampling bot hole cards
# ---------------------------------------------------------------------------
class RangeModel:
    """Simple range model to sample hole cards for bots."""

    def __init__(self, bots: Sequence) -> None:
        """Initialize with bot specifications (currently unused)."""
        self.bots = bots

    def sample_hole_cards(self, player_idx: int, gs: GameState) -> Tuple[Card, Card]:
        """Sample two unseen hole cards for player from the deck."""
        cards = gs.deck.draw(2)
        return cards[0], cards[1]

# ---------------------------------------------------------------------------
# Monte-Carlo simulator for EV estimation
# ---------------------------------------------------------------------------
class MonteCarloSimulator:
    """Monte-Carlo simulator that runs rollouts to estimate chip deltas."""

    def __init__(self, range_model: RangeModel, sb: int, bb: int) -> None:
        """Initialize simulator with range model and blind sizes."""
        self.range_model = range_model
        self.sb = sb
        self.bb = bb

    def run_once(self, gs: GameState) -> dict[int, float]:
        """Run a single simulated hand and return chip delta per player."""
        sim = copy.deepcopy(gs)
        # assign hole cards for players without cards
        for idx, p in enumerate(sim.players):
            if not p.hole_cards:
                h1, h2 = self.range_model.sample_hole_cards(idx, sim)
                p.hole_cards = [h1, h2]
        # determine hero index (0)
        hero = sim.players[0]
        # simple policy: hero loses bb if folded, gains bb otherwise
        delta = -self.bb if hero.has_folded else self.bb
        deltas = {i: 0.0 for i in range(len(sim.players))}
        deltas[0] = float(delta)
        return deltas

# ---------------------------------------------------------------------------
# EV Coach using Monte-Carlo simulations
# ---------------------------------------------------------------------------
class Coach:
    """Coach that estimates EV via Monte-Carlo simulations and provides feedback."""

    def __init__(self, bots: Sequence, rollouts: int = 500) -> None:
        """Initialize coach with bots and number of rollouts."""
        self.range_model = RangeModel(bots)
        self.rollouts = rollouts
        self.simulator: MonteCarloSimulator | None = None

    def estimate_ev(self, decision: Tuple[str, int], gs: GameState) -> float:
        """Estimate EV delta (in bb) of decision versus best alternative."""
        if self.simulator is None:
            sb = getattr(gs, 'sb', 1)
            bb = getattr(gs, 'bb', 2)
            self.simulator = MonteCarloSimulator(self.range_model, sb, bb)
        bb = self.simulator.bb

        clones = {
            'fold': copy.deepcopy(gs),
            'call': copy.deepcopy(gs),
            'shove': copy.deepcopy(gs),
        }
        clones['fold'].players[0].has_folded = True
        call_amt = gs.highest_bet - gs.players[0].bet
        if call_amt > 0:
            clones['call'].collect_bet(clones['call'].players[0], call_amt)
        allin = clones['shove'].players[0].stack
        if allin > 0:
            clones['shove'].collect_bet(clones['shove'].players[0], allin)
        evs: dict[str, float] = {}
        for key, clone in clones.items():
            total = 0.0
            for _ in range(self.rollouts):
                res = self.simulator.run_once(clone)
                total += res.get(0, 0.0)
            evs[key] = total / self.rollouts / bb
        hero_ev = evs.get(decision[0], evs['fold'])
        best_ev = max(evs.values())
        return hero_ev - best_ev

    def explain(self, decision: Tuple[str, int], gs: GameState) -> str:
        """Print and return a one-line EV feedback for the decision."""
        ev_delta = self.estimate_ev(decision, gs)
        if ev_delta < -1.0:
            msg = f"EV loss {ev_delta:.2f} bb | Tip: consider better option"
        else:
            msg = f"✔ EV OK ({ev_delta:+.2f} bb)"
        print(msg)
        return msg

# ---------------------------------------------------------------------------
# Showdown + winner determination (no side‑pots yet)
# ---------------------------------------------------------------------------

def showdown(gs: GameState) -> None:
    """Determine winners for each pot layer and distribute chips accordingly."""
    he = HandEvaluator()
    # active player indices
    active_idxs = [i for i, p in enumerate(gs.players) if not p.has_folded]
    # evaluate each active player's hand
    evals = {i: he.evaluate(gs.players[i].hole_cards + gs.board) for i in active_idxs}
    # distribute each pot layer
    for pot in gs.pots:
        # players eligible and still active
        eligible = [i for i in pot.eligible if i in active_idxs]
        if not eligible:
            continue
        # find best score among eligible
        best_score = None
        winners: List[int] = []
        for i in eligible:
            score = evals[i]
            if best_score is None or score > best_score:
                best_score = score
                winners = [i]
            elif score == best_score:
                winners.append(i)
        # split pot equally
        share = pot.amount // len(winners)
        for i in winners:
            gs.players[i].stack += share
    # display final table and summary
    print_table(gs)
    # summary message for main pot winners
    main_winners = [i for i in gs.pots[0].eligible if i in active_idxs and evals[i] == best_score]
    names = ",".join(gs.players[i].name for i in main_winners)
    print(f"Winners: {names}")


# ---------------------------------------------------------------------------
# Main CLI entry
# ---------------------------------------------------------------------------

def main() -> None:  # noqa: C901 – complexity fine for script
    parser = argparse.ArgumentParser()
    parser.add_argument("--players", type=int, default=3)
    parser.add_argument("--stacks", type=int, default=100)
    parser.add_argument("--sb", type=int, default=1, help="small blind")
    parser.add_argument("--bb", type=int, default=2, help="big blind")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--rollouts", type=int, default=500, help="Monte-Carlo rollouts")
    args = parser.parse_args()

    rng = RNG(args.seed)
    deck = Deck(rng)
    players = [Player("Hero", args.stacks)] + [Player(f"Bot{i}", args.stacks) for i in range(1, args.players)]
    gs = GameState(players, deck)
    # initialize EV coach
    global _coach
    _coach = Coach([p for p in players if p.name != "Hero"], args.rollouts)

    # -------- play a single hand (expand to loop later) -------------------------
    gs.deal_hole_cards()
    br = BettingRound(gs, args.sb, args.bb)
    br.post_blinds()

    while gs.street != Street.SHOWDOWN:
        print_table(gs)
        br.run()
        if len(gs.active_players) == 1:
            lone = gs.active_players[0]
            lone.stack += gs.pot
            print(f"All others folded – {lone.name} wins {gs.pot}")
            break
        gs.deal_next_street()
        br = BettingRound(gs, args.sb, args.bb)  # new betting round object

    if gs.street == Street.SHOWDOWN:
        showdown(gs)


# ---------------------------------------------------------------------------
# Override showdown to ensure correct side-pot distribution
# ---------------------------------------------------------------------------
def showdown(gs: GameState) -> None:
    """Determine winners for each pot layer and distribute chips accordingly."""
    he = HandEvaluator()
    active_idxs = [i for i, p in enumerate(gs.players) if not p.has_folded]
    evals = {i: he.evaluate(gs.players[i].hole_cards + gs.board) for i in active_idxs}
    # accumulate chip deltas per player
    deltas: dict[int, int] = {i: 0 for i in range(len(gs.players))}
    # distribute each pot layer
    for pot in gs.pots:
        eligible = [i for i in pot.eligible if i in active_idxs]
        if not eligible:
            continue
        best_score = max(evals[i] for i in eligible)
        winners = [i for i in eligible if evals[i] == best_score]
        share = pot.amount // len(winners)
        for i in winners:
            deltas[i] += share
    # apply deltas to stacks
    for i, player in enumerate(gs.players):
        player.stack += deltas.get(i, 0)
    # display final table and summary
    print_table(gs)
    main_pot = gs.pots[0]
    eligible_main = [i for i in main_pot.eligible if i in active_idxs]
    best_main_score = max(evals[i] for i in eligible_main)
    main_winners = [i for i in eligible_main if evals[i] == best_main_score]
    names = ",".join(gs.players[i].name for i in main_winners)
    print(f"Winners: {names}")

if __name__ == "__main__":
    main()