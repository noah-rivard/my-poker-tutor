import copy
from poker_tutor import GameState, Player, Deck, RNG, Coach, Street

def tiny_clone_gs():
    rng = RNG(3)
    deck = Deck(rng)
    gs = GameState([Player("Hero", 100), Player("Bot1", 100)], deck)
    gs.deal_hole_cards()
    return gs

def test_ev_sign_correct_direction():
    gs = tiny_clone_gs()
    coach = Coach([])
    hero = gs.players[0]
    # Force a terrible decision: hero folds with nuts (we fake nuts later)
    ev_loss = coach.estimate_ev(("fold", 0), copy.deepcopy(gs))
    assert ev_loss < 0  # folding should be negative EV

def test_rollout_stability():
    gs = tiny_clone_gs()
    coach = Coach([])
    ev1 = coach.estimate_ev(("call", 0), copy.deepcopy(gs))
    ev2 = coach.estimate_ev(("call", 0), copy.deepcopy(gs))
    assert abs(ev1 - ev2) < 0.5  # Monte-Carlo noise bounded