"""AI opponents using pokerkit equity calculations."""

from concurrent.futures import ProcessPoolExecutor
from typing import List, Iterable

from pokerkit import calculate_equities, parse_range
from pokerkit.utilities import Deck
from pokerkit.hands import StandardHighHand
from pokerkit.utilities import Card as PKCard


def estimate_equity(ranges: Iterable[str], board_cards: Iterable[str] = (),
                    sample_count: int = 1000) -> List[float]:
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
            tuple(PKCard.parse(c) for c in board_cards),
            2,  # hole cards dealt to each player
            5,  # total board cards
            Deck.STANDARD,
            (StandardHighHand,),
            sample_count=sample_count,
            executor=executor,
        )
    return eqs
