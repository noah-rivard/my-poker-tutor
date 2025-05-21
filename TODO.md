# TODO: Roadmap to Full Poker Simulator

This document outlines a potential path to evolve **my-poker-tutor** into a fully operational No Limit Hold'em simulator with AI opponents and comprehensive hand histories.

**Integrate AI Player Strategies**
   - Start with simple rule-based bots for basic decisions.
   - Add equity calculations using `pokerkit` to guide betting choices.
   - Explore more advanced approaches such as Monte Carlo Tree Search or reinforcement learning.
   - Fix `ai.py` helper functions which currently contain duplicate code and syntax errors.

**Persist Hand Histories**
   - Provide an export format (e.g., JSON or text) for later analysis.
   - Include options to load and review past sessions.

**Enhance the GUI**
   - Display stacks, bets, and pot amounts visually.

**TexasSolver Integration**
   - Explore using `console_solver.exe` from `TexasSolver-v0.2.0-Windows` to solve specific game states.
   - Provide a basic wrapper in `texas_solver.py` that generates parameter files
     and runs the solver.
   - Create a Python wrapper to generate parameter files and parse solver output.
   - Connect solver results to `PokerEngine` so the AI can request optimal lines in real time.
   - Precompute solutions for common spots using the provided ranges and cache them for quick lookup.
   - Document how to run the Windows binaries on other platforms (e.g., via Wine).

These steps provide a roadmap toward a more complete poker simulator with AI bots and analytics capabilities.
   - Remove duplicate function definitions in `texas_solver.py` which currently
     defines helpers like `simple_parameter_file` twice.
