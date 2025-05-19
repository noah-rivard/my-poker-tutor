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

## Solving Spots with TexasSolver

The repository bundles TexasSolver binaries under `TexasSolver-v0.2.0-Windows`.  
Use the helper functions in `texas_solver.py` to create parameter files and call
`console_solver.exe` from Python.

```python
from texas_solver import simple_parameter_file, run_console_solver

params = simple_parameter_file(
    pot=50,
    stack=200,
    board=["Qs", "Jh", "2h"],
    range_oop="JJ,TT,99",
    range_ip="AK,AQ",
    output_path="spot.txt",
)

output = run_console_solver(params)
print(output)
```

Running the solver requires Windows or a `wine` installation on other
platforms.
