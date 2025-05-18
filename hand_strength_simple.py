"""Lightweight Monte Carlo hand strength calculator using pokerkit."""

from __future__ import annotations

import random
from typing import Iterable, List

from pokerkit.pokerkit.hands import StandardHighHand
from pokerkit.pokerkit.utilities import Card as PKCard
from pokerkit.pokerkit.utilities import Deck


def _parse_cards(cards: Iterable[str]) -> List[PKCard]:
    """Parse a sequence of card strings into ``PKCard`` objects."""
    return [next(PKCard.parse(c)) for c in cards]


def monte_carlo_strength(
    hole_cards: Iterable[str],
    board_cards: Iterable[str] | None = None,
    num_opponents: int = 1,
    iterations: int = 1000,
    seed: int | None = None,
) -> float:
    """Estimate hand strength via Monte Carlo simulation.

    Parameters
    ----------
    hole_cards : iterable of str
        Two-character card strings like ``"As"``.
    board_cards : iterable of str, optional
        Already dealt community cards.
    num_opponents : int, optional
        Number of random opponents, defaults to ``1``.
    iterations : int, optional
        Number of Monte Carlo iterations, defaults to ``1000``.
    seed : int, optional
        Optional random seed for reproducibility.

    Returns
    -------
    float
        Fraction of iterations the hero hand wins, counting ties as a half
        win.
    """
    rng = random.Random(seed)

    hero = _parse_cards(hole_cards)
    board_known = _parse_cards(board_cards or [])

    base_deck = [card for card in Deck.STANDARD if card not in hero + board_known]

    wins = 0
    ties = 0

    for _ in range(iterations):
        deck = base_deck.copy()
        rng.shuffle(deck)

        board = list(board_known)
        while len(board) < 5:
            board.append(deck.pop())

        opp_holes = [ [deck.pop(), deck.pop()] for _ in range(num_opponents) ]

        hero_hand = StandardHighHand.from_game(hero, board)
        opp_hands = [StandardHighHand.from_game(o, board) for o in opp_holes]
        best_opp = max(opp_hands)

        if hero_hand > best_opp:
            wins += 1
        elif hero_hand == best_opp:
            ties += 1

    return (wins + 0.5 * ties) / iterations


if __name__ == "__main__":
    strength = monte_carlo_strength(["As", "Ac"], iterations=1000, seed=42)
    print(f"Strength: {strength:.3f}")
