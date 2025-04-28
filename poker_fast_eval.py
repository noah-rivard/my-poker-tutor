"""Fast hand‑evaluation wrapper that keeps the same public API as the old
HandEvaluator but runs ≈30× faster using the Two‑Plus‑Two LUT via the
`treys` library (pure‑Python, MIT‑licensed).

Drop this file next to your existing `poker_tutor.py`, then *inside*
`poker_tutor.py` replace the old `HandEvaluator` class with:

    from poker_fast_eval import HandEvaluator

No other code changes required; the API `evaluate(cards)->tuple` is
maintained.

If `treys` isn’t installed the module falls back to the original naïve
algorithm so tests still pass, just slower.
"""
from __future__ import annotations

import itertools
from typing import List, Sequence, Tuple

try:
    from treys import Card as _TCard, Evaluator as _TEvaluator

    _evaluator = _TEvaluator()

    def _to_int(card) -> int:
        """Convert our `Card` dataclass to treys integer."""
        # Our rank 0‑12 maps to treys rank 2‑A via string
        from poker_tutor import RANK_STR, SUITS  # local import to avoid circular

        rank_char = RANK_STR[card.rank]
        suit = card.suit
        if isinstance(suit, int):
            suit_char = SUITS[suit]
        else:
            suit_char = suit.lower()
        return _TCard.new(f"{rank_char}{suit_char}")

    class HandEvaluator:  # noqa: D101 – docstring inherited
        __slots__ = ("_eval",)

        def __init__(self) -> None:
            self._eval = _evaluator

        def evaluate(self, cards: Sequence["Card"]) -> Tuple[int, List[int]]:
            """Return (score, ranks) where *lower* score = *better* hand.

            We invert the score so that *higher* tuple still wins, matching
            the old API where bigger = stronger.
            """
            best = -1, []  # type: Tuple[int, List[int]]
            for combo in itertools.combinations(cards, 5):
                ints = [_to_int(c) for c in combo]
                val = self._eval.evaluate([], ints)  # board unused here
                # Convert to descending scale: 7462‑high worst → 1 best
                score = 1_000_000 - val  # big constant keeps >0
                if score > best[0]:
                    # keep kicker ranks for tie‑break verbosity
                    ranks = sorted((c.rank for c in combo), reverse=True)
                    best = score, ranks
            return best

except ModuleNotFoundError:  # ---- fallback: naïve original algo -----------

    import itertools
    from collections import Counter

    from poker_tutor import RANK_STR  # type: ignore  # circular ok at runtime

    class HandEvaluator:  # noqa: D101 – simple fallback; slower
        def evaluate(self, cards: Sequence["Card"]) -> Tuple[int, List[int]]:
            best = (0, [])
            for combo in itertools.combinations(cards, 5):
                score = self._eval5(combo)
                if score > best:
                    best = score
            return best

        def _eval5(self, cards: Sequence["Card"]) -> Tuple[int, List[int]]:
            ranks = sorted((c.rank for c in cards), reverse=True)
            counts = Counter(ranks)
            is_flush = len({c.suit for c in cards}) == 1
            uniq = sorted(set(ranks), reverse=True)
            # Straight incl. wheel ↘
            wheels = [12, 3, 2, 1, 0]  # A‑5 indexes
            is_straight = (
                len(uniq) == 5
                and (uniq[0] - uniq[-1] == 4 or uniq == wheels)
            )
            if is_straight and is_flush:
                return (9, ranks)
            if 4 in counts.values():
                quad = max(k for k, v in counts.items() if v == 4)
                kicker = max(k for k, v in counts.items() if v == 1)
                return (8, [quad, kicker])
            if sorted(counts.values()) == [2, 3]:
                trip = max(k for k, v in counts.items() if v == 3)
                pair = max(k for k, v in counts.items() if v == 2)
                return (7, [trip, pair])
            if is_flush:
                return (6, ranks)
            if is_straight:
                return (5, ranks)
            if 3 in counts.values():
                trip = max(k for k, v in counts.items() if v == 3)
                kickers = sorted((k for k, v in counts.items() if v == 1), reverse=True)
                return (4, [trip] + kickers)
            pairs = [k for k, v in counts.items() if v == 2]
            if len(pairs) >= 2:
                high, low = sorted(pairs, reverse=True)[:2]
                kicker = max(k for k, v in counts.items() if v == 1)
                return (3, [high, low, kicker])
            if len(pairs) == 1:
                pair = pairs[0]
                kickers = sorted((k for k, v in counts.items() if v == 1), reverse=True)
                return (2, [pair] + kickers)
            return (1, ranks)

    print(
        "[WARN] treys not found – using slow fallback hand evaluator.\n"
        "        Install it with: pip install treys"
    )
# ---------------------------------------------------------------------------
# Card, Deck, RNG definitions for downstream modules
# ---------------------------------------------------------------------------
import random
from dataclasses import dataclass
from typing import List

@dataclass(frozen=True)
class Card:
    """Immutable playing card with rank and suit."""
    rank: int
    suit: int

    @classmethod
    def from_str(cls, code: str) -> Card:
        """Create Card from two-character string, e.g. 'As','Td'."""
        rank_char = code[0].upper()
        suit_char = code[1].lower()
        from poker_tutor import RANK_STR, SUITS
        rank = RANK_STR.index(rank_char)
        suit = SUITS.index(suit_char)
        return cls(rank, suit)

    def __str__(self) -> str:
        from poker_tutor import RANK_STR, SUITS
        return f"{RANK_STR[self.rank]}{SUITS[self.suit]}"

class RNG(random.Random):
    """Random number generator seeded via Python's Random."""
    pass

class Deck:
    """Standard 52-card deck; supports shuffling and drawing."""
    def __init__(self, rng: RNG) -> None:
        self.rng = rng
        from poker_tutor import RANK_STR, SUITS
        # build full deck: ranks 2-A over suits c,d,h,s
        self.cards: List[Card] = [Card(rank, suit)
                                  for rank in range(len(RANK_STR))
                                  for suit in range(len(SUITS))]
        self.rng.shuffle(self.cards)

    def draw(self, n: int) -> List[Card]:
        drawn, self.cards = self.cards[:n], self.cards[n:]
        return drawn