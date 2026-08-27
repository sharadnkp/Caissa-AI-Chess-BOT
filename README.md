![Caïssa Banner](assets/banner.png)

# ♟️ Caïssa – AI Chess Engine

A Python-based chess engine powered by Minimax + Alpha-Beta pruning, built with Pygame — now with an evaluation function tuned by **reinforcement learning** through self-play.

---

## 🚀 Features

- ✔ **Three Game Modes**
  - Player vs Player (PvP)
  - Player vs AI (PvAI)
  - AI vs AI (AiAi)

- ✔ **Full Chess Rule Support**
  - Legal move generation
  - Castling
  - En passant
  - Pawn promotion
  - Check / Checkmate detection
  - Move validation

- ✔ **AI Engine**
  - Minimax with Alpha-Beta pruning
  - Depth configurable
  - Weighted-feature positional evaluation (material, mobility, center control, king safety, development)
  - Quiescence search (optional)

- ✔ **Reinforcement Learning (New)**
  - Evaluation weights tuned via **TD-Leaf self-play** instead of hand-picked values
  - Material values kept fixed (already well-established in chess); positional features (mobility, center control, king safety, development) are the ones actually learned
  - Includes a training script to re-run self-play and re-tune weights yourself

- ✔ **Graphics**
  - Board and piece rendering using Pygame
  - Smooth move animations (if enabled)

- ✔ **Code Structure**
  - Modular design
  - Clear separation between:
    - Engine
    - Board representation
    - AI
    - GUI
    - Game loop
  - Beginner-friendly with comments

---

## 📁 Project Structure

```
Caissa-AI-Chess-BOT/
│
├── Caissa_Chess_Engine_Presentation
│
├── assets/
│   ├── pieces/              # Chess piece sprites
│   ├── banner.png           # Project banner
│   └── logo.png             # Project logo
│
├── engine/
│   ├── chessEngine.py       # Board logic, move generation, check/checkmate
│   ├── SmartMoveFinder.py   # AI engine: NegaMax + Alpha-Beta pruning
│   ├── evaluation.py        # Weighted-feature evaluation (RL-tuned)
│   ├── td_train.py          # Self-play training loop (TD-Leaf)
│   ├── learned_weights.json # The actual learned weights
│   └── __init__.py
│
├── gui/
│   ├── chessMain.py         # Pygame main loop (entry point)
│   └── __init__.py
│
├── archive/
│   └── backup.py            # Archived/old code (not part of core)
│
├── LICENSE
├── requirements.txt
├── RL_INTEGRATION.md        # Full explanation of the RL training approach
├── README.md
└── .gitignore
```

---

## 🛠️ Installation

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/sharadnkp/Caissa-AI-Chess-BOT
cd Caissa-AI-Chess-BOT
```

### 2️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

> **Note:** pygame sometimes needs to compile from source depending on your Python version, which requires the SDL2 system library. If installation fails, install SDL2 first (macOS, via Homebrew):
> ```bash
> brew install sdl2 sdl2_image sdl2_mixer sdl2_ttf pkg-config
> pip install pygame
> ```

### ▶️ Running the Game

```bash
python gui/chessMain.py
```

---

## 🧠 Reinforcement Learning: Re-training the Weights

The evaluation weights can be re-tuned yourself via self-play:

```bash
python -m engine.td_train --games 300 --depth 1 --alpha 0.0005
```

In short: Caïssa plays itself many times, and after each move compares how
good a position looked before the search versus what the deeper search
actually found. The difference nudges the evaluation weights toward values
that better predict real outcomes — a simplified version of **TD-Leaf**, the
method behind KnightCap, one of the first engines to learn via self-play.

**Honest results from the current `learned_weights.json`** (300 self-play
games, depth 1):

```
material:        1.0   (fixed, not learned — see note below)
mobility:        -0.27
center_control:   0.10
extended_center: -0.14
king_safety:      0.02
development:      0.13
```

`center_control`, `king_safety`, and `development` learned positive
weights, matching real chess intuition. `mobility` and `extended_center`
learned negative weights, which is counter-intuitive — a real limitation of
shallow-depth, few-game training rather than a sign the mechanism is broken.

**Why material is fixed, not learned:** early testing let material update
like every other feature, and after a few hundred depth-1 self-play games it
drifted toward *negative* values — i.e. the engine "learning" that losing
pieces is good. Material values in chess are already well-established
(queen=9, rook=5, etc.), so there's nothing genuinely uncertain there for RL
to discover. Learning is instead focused on the positional features, where
real uncertainty exists.

See `RL_INTEGRATION.md` for the full technical explanation.

---

## ⚙️ Configuration

You can tweak the engine in the configuration section of the code:

- AI depth
- Animation toggle
- Theme
- AI vs AI speed
- Evaluation tuning (via re-training)

---

## 🖼️ Screenshot

**Interface:**

![Caïssa Interface](screenshots/board.png)

---

## 🧩 Future Improvements

- Stronger evaluation function (more features: pawn structure, rook on open file, etc.)
- Opening book
- Transposition table
- Endgame tablebases
- Zobrist hashing
- PGN/FEN import & export
- Online multiplayer support
- **Online learning**: currently the AI only learns from offline self-play training runs, not from games people actually play against it — hooking real games into the same TD-Leaf update loop is a natural next step
- Deeper self-play training (more games, higher search depth) to correct the counter-intuitive mobility/extended-center weights noted above

---

## 🤝 Contributing

Pull requests are welcome! Just make sure your code is clean and modular.

---

## 📜 License

This project is licensed under the MIT License. You are free to use, modify, and distribute.

---

## ⭐ Support the Project

If you like Caïssa, please star ⭐ the repo — it motivates development!
