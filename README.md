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

Hand histories from each game can be saved with:
```
from engine import PokerEngine
eng = PokerEngine()
eng.new_hand()
... # play some actions
eng.save_histories("hand_history.json")
```
