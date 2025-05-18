"""Helper utilities for AI calculations using PokerKit."""

from concurrent.futures import ProcessPoolExecutor
import random
from typing import Iterable, List, Tuple

from engine import PokerEngine


from pokerkit import (
    calculate_equities,
    calculate_hand_strength,
    parse_range,
)
from pokerkit.pokerkit.hands import StandardHighHand
from pokerkit.pokerkit.utilities import Card as PKCard
from pokerkit.pokerkit.utilities import Deck


def estimate_equity(
    ranges: Iterable[str], board_cards: Iterable[str] = (), sample_count: int = 1000
) -> List[float]:
    """Estimate player equities using Monte Carlo simulation.

    Parameters
    ----------
    ranges : iterable of str
        Hand ranges for each active player written in pokerkit range syntax.
    board_cards : iterable of str, optional
        Board cards already dealt in two-character notation like ``'As'``.
    sample_count : int, optional
        Number of Monte Carlo samples to run, defaults to 1000.

    Returns
    -------
    list of float
        The estimated equity for each player.
    """
    board = [next(PKCard.parse(c)) for c in board_cards]

    with ProcessPoolExecutor() as executor:
        eqs = calculate_equities(
            tuple(parse_range(r) for r in ranges),
            board,
            2,  # hole cards dealt to each player
            5,  # total board cards
            Deck.STANDARD,
            (StandardHighHand,),
            sample_count=sample_count,
            executor=executor,
        )
    return eqs


def estimate_equity_vs_random(
    hole_cards: Iterable[str],
    board_cards: Iterable[str] = (),
    player_count: int = 2,
    sample_count: int = 1000,
) -> float:
    """Estimate equity of ``hole_cards`` versus random opponents."""

    ranges = [[[]] for _ in range(player_count - 1)]
    hole = [next(PKCard.parse(c)) for c in hole_cards]
    ranges.append([hole])
    board = [next(PKCard.parse(c)) for c in board_cards]

    with ProcessPoolExecutor() as executor:
        eqs = calculate_equities(
            ranges,
            board,
            2,
            5,
            Deck.STANDARD,
            (StandardHighHand,),
            sample_count=sample_count,
            executor=executor,
        )

    return eqs[-1]


def estimate_hand_strength(
    hole_cards: Iterable[str],
    board_cards: Iterable[str] = (),
    player_count: int = 2,
    sample_count: int = 1000,
) -> float:
    """Shortcut around :func:`calculate_hand_strength`."""

    hole_range = parse_range("".join(hole_cards))
    board = [next(PKCard.parse(c)) for c in board_cards]

    with ProcessPoolExecutor() as executor:
        strength = calculate_hand_strength(
            player_count,
            hole_range,
            board,
            2,
            5,
            Deck.STANDARD,
            (StandardHighHand,),
            sample_count=sample_count,
            executor=executor,
        )

    return strength


def basic_ai_decision(
    engine: PokerEngine,
    seat: int,
    rng: random.Random | None = None,
    sample_count: int = 200,
) -> Tuple[str, int]:
    """Choose a simple action for the bot at ``seat``.

    The decision is based on a quick Monte Carlo equity estimate.
    """

    rng = rng or random

    hole = engine.hole_cards.get(seat)
    if not hole:
        return "check", 0

    hole_strs = [engine._tuple_to_str(c) for c in hole]
    board_strs = [engine._tuple_to_str(c) for c in engine.community]
    player_count = sum(engine.active)

    try:
        strength = estimate_hand_strength(
            hole_strs,
            board_strs,
            player_count,
            sample_count=sample_count,
        )
    except Exception:
        strength = 0.5

    to_call = engine.current_bet - engine.contributions[seat]
    facing_bet = to_call > 0

    if facing_bet:
        if strength < 0.2:
            return ("fold", 0) if rng.random() < 0.8 else ("call", 0)
        if strength < 0.5:
            return "call", 0
        if strength < 0.75:
            return ("raise", engine.bb_amt * 2) if rng.random() < 0.3 else ("call", 0)
        return ("raise", engine.bb_amt * 3) if rng.random() < 0.7 else ("call", 0)

    if strength > 0.6 and rng.random() < 0.6:
        return "bet", engine.bb_amt * 2
    return "check", 0

