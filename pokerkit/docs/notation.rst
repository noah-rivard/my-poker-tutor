Hand History
============

PokerKit can save and/or load hand histories in two formats: the `Poker Hand History (PHH) file format <https://phh.readthedocs.io/>`_, the `Annual Computer Poker Competition (ACPC) protocol <_static/protocol.pdf>`_, and the protocol used in the supplementary of the paper introducing `Pluribus <https://doi.org/10.1126/science.aay2400>`_.

Poker Hand History (PHH) File Format
------------------------------------

The PokerKit library features `PHH file format <https://phh.readthedocs.io/>`_ reader and writer utilities. It offers "load" and "dump" programmatic APIs akin to those provided by Python's standard libraries such as "json," and "pickle". Below are sample usages of the PHH file format utilities in PokerKit. The hand history object in Python serves as an iterator of the corresponding poker state which first yields the initial state, followed by the same state after applying each action one-by-one in the “actions” field. From game and state objects that are interacted with programmatically, the hand history object can also be created which can subsequently be saved in the file system.

Reading hands
^^^^^^^^^^^^^

.. code-block:: python

   from pokerkit import *

   # Load hand
   with open("path/to/file.phh", "rb") as file:
       hh = HandHistory.load(file)

   # Create game
   game = hh.create_game()

   # Create state
   state = hh.create_state()

   # Iterate through each action step
   for state in hh:
       ...

   # Iterate through each action step
   for state, action in hh.state_actions:
       ...

If you have multiple hands in a single file, they can be loaded together.

.. code-block:: python

   from pokerkit import *

   # Load hands
   with open("path/to/file.phhs", "rb") as file:
       hhs = HandHistory.load_all(file)

   # Iterate through each hand history
   for hh in hhs:
       ...

Logs from third-party platforms like online casinos or research environments can be loaded as well. Feel free to open an issue if incompatibilities are found.

Supported Platforms are tabulated below.

================================================= ==========================================================
Platform                                          Method
================================================= ==========================================================
Absolute Poker                                    :func:`pokerkit.notation.HandHistory.from_absolute_poker`
Full Tilt Poker                                   :func:`pokerkit.notation.HandHistory.from_full_tilt_poker`
iPoker Network                                    :func:`pokerkit.notation.HandHistory.from_ipoker_network`
OnGame Network                                    :func:`pokerkit.notation.HandHistory.from_ongame_network`
PartyPoker                                        :func:`pokerkit.notation.HandHistory.from_partypoker`
PokerStars                                        :func:`pokerkit.notation.HandHistory.from_pokerstars`
ACPC (Annual Computer Poker Competition) Protocol :func:`pokerkit.notation.HandHistory.from_acpc_protocol`
================================================= ==========================================================

.. code-block:: python

   from pokerkit import *

   # Hand loading
   with open("...", "rb") as file:
       content = file.read()

       # Absolute Poker
       for hh in HandHistory.from_absolute_poker(content):
           ...

       # Full Tilt Poker
       for hh in HandHistory.from_full_tilt_poker(content):
           ...

       # iPoker Network
       for hh in HandHistory.from_ipoker_network(content):
           ...

       # OnGame Network
       for hh in HandHistory.from_ongame_network(content):
           ...

       # PartyPoker
       for hh in HandHistory.from_partypoker(content):
           ...

       # PokerStars
       for hh in HandHistory.from_pokerstars(content):
           ...

       # ACPC Protocol
       for hh in HandHistory.from_acpc_protocol(
               content,
               NoLimitTexasHoldem((), True, 0, (50, 100), 100),
               20000,
       ):
           ...

It is possible to supply your own chip value parsing function, divmod, or rake function to construct the game states. Additionally, the default value parsing function is defined as :func:`pokerkit.utilities.parse_value`. This parser automatically parses integers or floats based on the raw string value. You may supply your own number-type parsers as well.

.. code-block:: python

   from pokerkit import *

   hh = HandHistory.load(
       ...,
       automations=...,
       divmod=...,
       rake=...,
       parse_value=...,
   )

   hh = HandHistory.loads(
       ...,
       automations=...,
       divmod=...,
       rake=...,
       parse_value=...,
   )

Writing Hands
^^^^^^^^^^^^^

.. code-block:: python

   from pokerkit import *

   # Game state construction
   game = PotLimitOmahaHoldem(
       (
           Automation.ANTE_POSTING,
           Automation.BET_COLLECTION,
           Automation.BLIND_OR_STRADDLE_POSTING,
           Automation.CARD_BURNING,
           Automation.HOLE_CARDS_SHOWING_OR_MUCKING,
           Automation.HAND_KILLING,
           Automation.CHIPS_PUSHING,
           Automation.CHIPS_PULLING,
       ),
       True,
       0,
       (500, 1000),
       1000,
   )
   state = game((1259450.25, 678473.5), 2)

   # State progression; Pre-flop
   state.deal_hole("Ah3sKsKh")  # Antonius
   state.deal_hole("6d9s7d8h")  # Blom
   state.complete_bet_or_raise_to(3000)  # Blom
   state.complete_bet_or_raise_to(9000)  # Antonius
   state.complete_bet_or_raise_to(27000)  # Blom
   state.complete_bet_or_raise_to(81000)  # Antonius
   state.check_or_call()  # Blom

   # Flop
   state.deal_board("4s5c2h")
   state.complete_bet_or_raise_to(91000)  # Antonius
   state.complete_bet_or_raise_to(435000)  # Blom
   state.complete_bet_or_raise_to(779000)  # Antonius
   state.check_or_call()  # Blom

   # Turn & River
   state.deal_board("5h")
   state.deal_board("9c")

   # Creating hand history
   hh = HandHistory.from_game_state(game, state)
   hh.players = ["Patrik Antonius", "Viktor Blom"]

   # Dump hand
   with open("path/to/file.phh", "wb") as file:
       hh.dump(file)

If you have multiple hands, they can be dumped together in a single file.

.. code-block:: python

   from pokerkit import *

   hhs = [...]

   # Dump hands
   with open("path/to/file.phhs", "wb") as file:
       HandHistory.dump_all(hhs, file)

Annual Computer Poker Competition (ACPC) Protocol
-------------------------------------------------

Instead of saving hand histories as PHH files, `ACPC <_static/protocol.pdf>`_ logs can be generated.

.. code-block:: python

   hh = ...
   lines = [
       f'{sender} {message}' for sender, message in hh.to_acpc_protocol(0, 0)
   ]

   with open("...", "w") as file:
       file.write("".join(lines))

Pluribus Protocol
-----------------

This format was used to record games by `Brown and Sandholm <https://doi.org/10.1126/science.aay2400>`_ in the supplementary for their Science paper on Pluribus.

.. code-block:: python

   hh = ...
   line = hh.to_pluribus_protocol(10)

   with open("...", "w") as file:
       file.write(line)
