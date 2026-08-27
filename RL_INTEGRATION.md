# Reinforcement Learning for Caissa: TD-Leaf Self-Play

This adds real reinforcement learning to Caissa: the evaluation function's
weights are learned through self-play instead of hand-picked, using a
simplified version of **TD-Leaf** (the algorithm behind KnightCap, one of
the first engines to learn via self-play back in the late 1990s, before
neural network evaluation existed).

Your Minimax/Alpha-Beta **search is untouched** - this only changes how
positions are *scored*, not how the search explores the game tree.

## New files

- `engine/evaluation.py` - a weighted-feature evaluation function
  (material, mobility, center control, king safety, development) instead
  of pure material counting. The weights are what gets learned.
- `engine/td_train.py` - the self-play training loop.
- `engine/learned_weights.json` - created automatically once you train;
  holds the learned weights.

## How the learning actually works

1. Caissa plays a full game against itself.
2. At every move, the search's leaf evaluation (the score it settled on
   after looking `depth` moves ahead) is recorded, along with the feature
   values of that position.
3. After the move, we compare *this* leaf value to the *next* one. If the
   position turned out better than predicted, the weights nudge toward
   features that would have predicted that.
4. At the game's end, the real outcome (win/loss/draw) becomes the final
   target, so the learning signal connects all the way back through the
   game.

This is genuine reinforcement learning - no labeled data, no database of
human games, just self-play and the TD (temporal-difference) update rule.

## Running it

From the project root (the folder with `engine/` and `gui/` inside it):

```bash
pip install -r requirements.txt   # no new dependencies needed, just confirming your env
python -m engine.td_train --games 50 --depth 1 --alpha 0.001
```

### Important: be realistic about speed

This is pure Python with no move-generation optimizations (no bitboards,
no compiled extensions), so self-play is slow:

- **Depth 1**: ~1-3 seconds per game (very shallow, weaker signal, but you
  can run hundreds of games quickly to see the mechanism working)
- **Depth 2**: measured at ~2 seconds *per move* on this codebase, so a
  ~40-move game takes over a minute. 50 games at depth 2 could take
  1-2+ hours.
- **Depth 3** (the GUI's default): not realistic for training - only use
  this for actually playing, after weights are learned at a lower depth.

**Recommended first run**: start with `--depth 1 --games 100` to confirm
the weights are moving and the mechanism works end-to-end (takes a few
minutes), then decide if you want to let a slower `--depth 2` run go
overnight for a more meaningful result.

## Using the learned weights when actually playing

Once you've trained and `engine/learned_weights.json` exists, swap
`SmartMoveFinder.py`'s material-only `scoreBoard()` for the learned
evaluator:

```python
# at the top of SmartMoveFinder.py
from engine.evaluation import Evaluator
_evaluator = Evaluator()  # auto-loads learned_weights.json if present

# replace the body of scoreBoard(gs) with:
def scoreBoard(gs):
    return _evaluator.evaluate(gs, CHECKMATE, STALEMATE)
```

That's the only change needed to actually play with the learned weights -
the rest of your search code (NegaMax, Alpha-Beta, move ordering) stays
exactly as it was.

## Honest caveats

- This is a **small, hand-picked feature set** (6 features). Real engines
  that use TD-Leaf successfully often have dozens of features (pawn
  structure, piece-square tables per piece type, rook-on-open-file, etc.).
  This is a solid, real starting point - not the ceiling of what's possible.
- Training is noisy with few games. Don't expect dramatic, stable
  improvement from 50-100 games - TD-Leaf papers typically report training
  over thousands of self-play games. Treat an initial run as a proof of
  concept, not a finished tuning.
- The mobility feature approximates legal moves using pseudo-legal move
  counts (not filtering for checks) purely for speed - this is a common
  simplification, but worth knowing about if you inspect the numbers.

## What this gives you to say, accurately

"Implemented TD-Leaf reinforcement learning to tune Caissa's evaluation
function weights via self-play, replacing the original hand-set material
values with a 6-feature weighted evaluation (material, mobility, center
control, king safety, development) learned through temporal-difference
updates over self-play games."

That's a specific, true, technically defensible claim - not a vague
"used AI to improve the engine."
