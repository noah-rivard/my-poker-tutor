import pytest
from poker_tutor import Player, GameState, Deck, RNG, BettingRound, showdown

def force_stacks():
    rng = RNG(1)
    deck = Deck(rng)
    A, B, C = Player("A", 100), Player("B", 200), Player("C", 400)
    gs = GameState([A, B, C], deck)
    gs.deal_hole_cards()
    br = BettingRound(gs, small_blind=1, big_blind=2)
    br.post_blinds()

    # force arbitrary bets to trigger two side-pots
    gs.collect_bet(A, 98)      # A all-in → 100 total
    gs.collect_bet(B, 198)     # B all-in → 200 total
    gs.collect_bet(C, 200)     # C covers both → 202 total
    gs.build_side_pots()       # layer-peel into [294, 202, 3]

    return gs, (A, B, C)

def test_sidepot_layers():
    gs, _ = force_stacks()
    sizes = [p.amount for p in gs.pots]
    assert sizes == [294, 202, 3]   # main, side-1, side-2

def test_showdown_payout(monkeypatch):
    gs, (A, B, C) = force_stacks()

    # rig evaluator so C always wins, B second, A last
    monkeypatch.setattr(
        "poker_tutor.HandEvaluator.evaluate",
        lambda self, cards: (3 if cards in C.hole_cards else 2 if cards in B.hole_cards else 1, [])
    )

    showdown(gs)   # run once

    # C: kept 198 behind + wins 499 = 697
    assert C.stack == 697
    # B: paid 199, wins nothing → 1 left
    assert B.stack == 1
    # A: paid 98, wins nothing → 2 left
    assert A.stack == 2