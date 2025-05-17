"""Configuration utilities for the poker engine."""

import json
from dataclasses import dataclass
from typing import Any

from engine import PokerEngine


@dataclass
class EngineConfig:
    """Simple dataclass holding engine configuration."""

    num_players: int = 6
    starting_stack: int = 1000
    sb_amt: int = 10
    bb_amt: int = 20


def load_config(path: str) -> EngineConfig:
    """Load engine configuration from a JSON file."""
    with open(path, "r", encoding="utf-8") as fh:
        data: Any = json.load(fh)
    return EngineConfig(**data)


def engine_from_config(path: str) -> PokerEngine:
    """Create a :class:`PokerEngine` using configuration from ``path``."""
    cfg = load_config(path)
    return PokerEngine(
        num_players=cfg.num_players,
        starting_stack=cfg.starting_stack,
        sb_amt=cfg.sb_amt,
        bb_amt=cfg.bb_amt,
    )
