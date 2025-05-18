# TODO: Roadmap to Full Poker Simulator

This document outlines a potential path to evolve **my-poker-tutor** into a fully operational No Limit Hold'em simulator with AI opponents and comprehensive hand histories.

1. **Expand the Betting Engine**
   - Support all No Limit Hold'em betting actions (bet, raise, call, fold, check).
   - Handle pot calculations, side pots, and stack management.
   - Implement turn order and stage transitions for preflop, flop, turn, and river.

2. **Integrate AI Player Strategies**
   - Start with simple rule-based bots for basic decisions.
   - Add equity calculations using `pokerkit` to guide betting choices.
   - Explore more advanced approaches such as Monte Carlo Tree Search or reinforcement learning.

3. **Persist Hand Histories**
   - Log each hand's actions, board runout, and results.
   - Provide an export format (e.g., JSON or text) for later analysis.
   - Include options to load and review past sessions.

4. **Enhance the GUI**
   - Allow players to select seats, buy in, and rebuy.
   - Display stacks, bets, and pot amounts visually.
   - Offer controls for user actions and bot speed settings.

5. **Add Configuration and Testing**
   - Make number of players, blinds, and stack sizes configurable.
   - Expand unit tests to cover edge cases in betting and game flow.
   - Consider CI pipelines to run tests automatically.

These steps provide a roadmap toward a more complete poker simulator with AI bots and analytics capabilities.

6. **Bug Fixes Needed**
   - The `SeatWidget` class defines `highlight` twice in `main.py`, so the
     earlier implementation that updates `_winner` is overwritten. This prevents
     the GUI from correctly highlighting winning seats.
   - After a betting round ends in `PokerEngine._end_betting_round`, the `turn`
     is always set to the seat left of the button without skipping folded or
     all-in players. This can cause an exception on the next action.
   - In `PokerEngine.player_action` handling of the `raise` action, a short
     stack can specify a raise larger than their stack. The resulting partial
     raise lowers `current_bet` to that player's contribution, leading to
     inconsistent bet amounts.

