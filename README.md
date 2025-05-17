# my-poker-tutor

Desktop Poker Simulation UI using PyQt5.

## Requirements
- Python 3.7+
- Install dependencies with:
```
pip install -r requirements.txt
```

## Usage
Run the simulation:
```
python main.py
```

The engine parameters can be customized with a JSON configuration file. A sample
`config.json` is provided:

```
{
  "num_players": 6,
  "starting_stack": 1000,
  "sb_amt": 10,
  "bb_amt": 20
}
```

You can create your own configuration and load it using:

```
from config import engine_from_config
engine = engine_from_config("my_config.json")
```


Hand histories from each game can be saved with:
```
from engine import PokerEngine
eng = PokerEngine()
eng.new_hand()
... # play some actions
eng.save_histories("hand_history.json")
```
