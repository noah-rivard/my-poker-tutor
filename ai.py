"""AI opponents using pokerkit equity calculations."""

from concurrent.futures import ProcessPoolExecutor
from typing import Iterable, List

from pokerkit import (
    calculate_equities,
    calculate_hand_strength,
    parse_range,
)
from pokerkit import calculate_equities, calculate_hand_strength, parse_range
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
    with ProcessPoolExecutor() as executor:
        eqs = calculate_equities(
            tuple(parse_range(r) for r in ranges),
            tuple(next(PKCard.parse(c)) for c in board_cards),
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

    hole = [PKCard.parse(c) for c in hole_cards]
    ranges.append([hole])
    board = [PKCard.parse(c) for c in board_cards]

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

    hole_range = [PKCard.parse(c) for c in hole_cards]
    board = [PKCard.parse(c) for c in board_cards]

    with ProcessPoolExecutor() as executor:
        strength = calculate_hand_strength(
            player_count,
    hole_range = [next(PKCard.parse(c)) for c in hole_cards]
    board = [next(PKCard.parse(c)) for c in board_cards]

    with ProcessPoolExecutor() as executor:
        strength = calculate_hand_strength(
            player_count,
    hole_range = parse_range(''.join(hole_cards))
    board = [next(PKCard.parse(c)) for c in board_cards]

    hole_range = [PKCard.parse(c) for c in hole_cards]
    board = [PKCard.parse(c) for c in board_cards]
    with ProcessPoolExecutor() as executor:
        strength = calculate_hand_strength(
            player_count,
            hole_range,
            [hole_range],
            board,
            2,
            5,
            Deck.STANDARD,
            (StandardHighHand,),
            sample_count=sample_count,
            executor=executor,
        )

    return strength
