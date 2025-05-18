"""Expose the actual PokerKit package bundled as a submodule."""

from importlib import import_module
from pathlib import Path
from pkgutil import extend_path

__path__ = extend_path(__path__, __name__)
__path__.append(str(Path(__file__).resolve().parent / "pokerkit"))

module = import_module(".pokerkit", __name__)
globals().update(module.__dict__)
