"""Helper utilities for AI calculations using PokerKit."""

from concurrent.futures import ProcessPoolExecutor
import random
import tempfile
from pathlib import Path
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
import texas_solver


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


def optimal_ai_move(
    engine: PokerEngine,
    seat: int,
    ranges: dict[int, str] | None = None,
    sample_count: int = 500,
) -> Tuple[str, int]:
    """Return a suggested action using simple equity and pot odds heuristics."""

    hole = engine.hole_cards.get(seat)
    if not hole:
        return "check", 0

    hole_strs = [engine._tuple_to_str(c) for c in hole]
    board_strs = [engine._tuple_to_str(c) for c in engine.community]
    to_call = max(0, engine.current_bet - engine.contributions[seat])
    pot = engine.pot

    active_seats = [i for i in range(engine.num_players) if engine.active[i]]

    if ranges:
        order = []
        for i in active_seats:
            if i == seat:
                order.append("".join(hole_strs))
            else:
                order.append(ranges.get(i, ""))
        try:
            equities = estimate_equity(order, board_strs, sample_count=sample_count)
            hero_equity = equities[active_seats.index(seat)]
        except Exception:
            hero_equity = 0.5
    else:
        try:
            hero_equity = estimate_hand_strength(
                hole_strs,
                board_strs,
                len(active_seats),
                sample_count=sample_count,
            )
        except Exception:
            hero_equity = 0.5

    pos_index = (seat - engine.button - 1) % engine.num_players
    position_bonus = 0.05 * pos_index / max(1, engine.num_players - 1)
    equity = min(1.0, max(0.0, hero_equity + position_bonus))

    pot_odds = to_call / (pot + to_call) if to_call else 0

    if to_call:
        if equity < pot_odds * 0.9:
            return "fold", 0
        if equity < pot_odds + 0.1:
            return "call", 0
        raise_amt = int(min(engine.stacks[seat] - to_call, max(engine.bb_amt, pot // 2)))
        if raise_amt <= 0:
            return "call", 0
        return "raise", raise_amt

    if equity <= 0.5:
        return "check", 0
    bet_amt = int(min(engine.stacks[seat], max(engine.bb_amt, pot // 2)))
    if equity > 0.7:
        bet_amt = int(min(engine.stacks[seat], max(engine.bb_amt * 2, (pot * 3) // 4)))
    if bet_amt <= 0:
        return "check", 0
    return "bet", bet_amt


def solver_ai_move(
    engine: PokerEngine,
    seat: int,
    *,
    hero_range: str,
    opp_range: str,
    exe_dir: str | Path = texas_solver.DEFAULT_EXE_DIR,
) -> Tuple[str, int]:
    """Use TexasSolver to suggest an action for ``seat``.

    Parameters
    ----------
    engine : PokerEngine
        Current game engine.
    seat : int
        Seat index of the acting player.
    hero_range : str
        Range string for the hero player.
    opp_range : str
        Range string for the opponent.
    exe_dir : str or Path, optional
        Directory containing ``console_solver.exe``.
    """

    hole = engine.hole_cards.get(seat)
    if not hole:
        return "check", 0

    board = [engine._tuple_to_str(c) for c in engine.community]
    hero_hand = "".join(engine._tuple_to_str(c) for c in hole)

    opp = 1 - seat if engine.num_players == 2 else (seat + 1) % engine.num_players
    stack = min(engine.stacks[seat], engine.stacks[opp])

    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
        params = texas_solver.simple_parameter_file(
            pot=engine.pot,
            stack=stack,
            board=board,
            range_oop=opp_range,
            range_ip=hero_range,
            output_path=tmp.name,
        )

    try:
        out = texas_solver.run_console_solver(params, exe_dir=exe_dir, timeout=15)
        action, amt = texas_solver.parse_solver_output(out, hero_hand)
    except Exception:
        action, amt = "check", 0
    finally:
        try:
            Path(params).unlink()
        except FileNotFoundError:
            pass

    return action, amt

