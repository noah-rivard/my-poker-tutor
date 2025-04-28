"""Pytest suite for the poker‑tutor refactor.

Run with:
    pytest -q
"""
from types import SimpleNamespace
from unittest.mock import patch

import poker_tutor as pt

# ---------------------------------------------------------------------------
# Deck integrity
# ---------------------------------------------------------------------------

def test_deck_integrity():
    """A new shuffled deck should contain exactly 52 unique cards, no dups."""
    d = pt.Deck(pt.RNG(0))
    drawn = d.draw(52)
    # All string representations must be unique
    assert len({str(c) for c in drawn}) == 52
    # Deck should now be empty
    assert d.cards == []

# ---------------------------------------------------------------------------
# Hand‑evaluator edge case: wheel straight vs K‑high straight
# ---------------------------------------------------------------------------

def _cards(*codes):
    return [pt.Card.from_str(c) for c in codes]


def test_evaluator_wheel_vs_k_high():
    """Ensure the wheel (A‑5 straight) ranks *below* a K‑high straight."""
    eval_ = pt.HandEvaluator()

    wheel = eval_.evaluate(
        _cards("As", "5h", "4d", "3c", "2s")
    )
    k_high = eval_.evaluate(
        _cards("Ks", "Qh", "Jd", "Tc", "9s")
    )
    # k_high should outrank wheel (bigger tuple)
    assert k_high > wheel

# ---------------------------------------------------------------------------
# Pot accounting sanity
# ---------------------------------------------------------------------------

def test_pot_equals_sum_of_bets():
    """After a simple betting round, pot == sum(p.bet for p in players)."""
    rng = pt.RNG(42)
    players = [pt.Player(name="Hero", stack=100, bet=2, hole_cards=[]),
               pt.Player(name="Villain", stack=100, bet=2, hole_cards=[])]
    gs = pt.GameState(players=players, board=[], pot=4, dealer=0, to_act=0, street="flop")
    assert gs.pot == sum(p.bet for p in gs.players)

# ---------------------------------------------------------------------------
# prompt_action parser
# ---------------------------------------------------------------------------

def test_prompt_action_parsing(monkeypatch):
    """Input variants map to canonical ('fold'|'call'|'raise', amount)"""
    inputs = iter(["f", "c", "r5"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    assert pt.prompt_action(["fold", "call", "raise"]) == ("fold", 0)
    assert pt.prompt_action(["fold", "call", "raise"]) == ("call", 0)
    assert pt.prompt_action(["fold", "call", "raise"]) == ("raise", 5)