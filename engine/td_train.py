"""
td_train.py

Trains Caissa's evaluation weights via TD(0)-on-leaf-values self-play,
a simplified version of TD-Leaf(lambda) (Baxter, Tridgell & Weaver's
KnightCap algorithm). This is real reinforcement learning: no labeled
data, no human game database - the engine improves purely by playing
itself and learning from the *change* in its own evaluations over time.

HOW IT WORKS
------------
1. Caissa plays a full game against itself using its existing depth-limited
   Alpha-Beta search (unchanged) - only the evaluation function's WEIGHTS
   are learned, the search algorithm itself is untouched.
2. At each move, we record the feature vector of the position the search
   settled on (the "leaf" value backing up to the root).
3. After the move is played, we compare the new leaf value the search
   returns to the previous one. The difference (the "temporal difference")
   is the learning signal: if the position looks better than the eval
   predicted, nudge the weights that would have predicted that.
4. At the end of the game, the true outcome (win/loss/draw) is used as the
   final target, which lets learning signal propagate backward through the
   whole game over many self-play games.

This keeps your Minimax/Alpha-Beta search completely intact - only
`evaluation.py`'s weights change.

USAGE
-----
    python -m engine.td_train --games 200 --depth 2 --alpha 0.001

Run this from the project root (the folder containing engine/ and gui/).
Depth 2 is used by default (rather than the GUI's DEPTH=3) purely for
training speed - you need hundreds of games for the weights to move
meaningfully, and pure-Python search is slow. Once weights are learned,
you can still search at depth 3+ when actually playing.
"""
import argparse
import random
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.chessEngine import GameState
from engine.evaluation import Evaluator, FEATURE_NAMES

CHECKMATE = 1000
STALEMATE = 0


def negamax_leaf(gs, evaluator, depth, alpha, beta, turn_multiplier):
    """Alpha-beta negamax search that, at the leaf, returns both the score
    AND the feature vector of the leaf position (needed for the TD update).
    Structurally identical to SmartMoveFinder's search - only the return
    value is extended to carry features back up.
    """
    if gs.checkmate or gs.stalemate:
        score = turn_multiplier * evaluator.evaluate(gs, CHECKMATE, STALEMATE)
        return score, evaluator.extract_features(gs)

    if depth == 0:
        features = evaluator.extract_features(gs)
        score = turn_multiplier * evaluator.evaluate_from_features(features)
        return score, features

    valid_moves = gs.getValidMoves()
    if len(valid_moves) == 0:
        features = evaluator.extract_features(gs)
        score = turn_multiplier * evaluator.evaluate(gs, CHECKMATE, STALEMATE)
        return score, features

    random.shuffle(valid_moves)
    max_score = -CHECKMATE - 1
    best_features = None

    for move in valid_moves:
        gs.makeMove(move)
        next_moves = gs.getValidMoves()
        score, features = negamax_leaf(gs, evaluator, depth - 1, -beta, -alpha, -turn_multiplier)
        score = -score
        gs.undoMove()

        if score > max_score:
            max_score = score
            best_features = features

        if max_score > alpha:
            alpha = max_score
        if alpha >= beta:
            break

    return max_score, best_features


def play_one_game(evaluator, depth, max_moves=150):
    """Plays one self-play game. Returns a list of (features, value) pairs
    -- one per ply -- where `value` is the search's leaf evaluation from
    White's perspective, plus the final game outcome (+1 / -1 / 0).
    """
    gs = GameState()
    history = []  # list of feature dicts, one per ply, White's perspective

    for _ply in range(max_moves):
        valid_moves = gs.getValidMoves()
        if gs.checkmate or gs.stalemate or len(valid_moves) == 0:
            break

        turn_multiplier = 1 if gs.whiteToMove else -1
        score, leaf_features = negamax_leaf(
            gs, evaluator, depth, -CHECKMATE - 1, CHECKMATE + 1, turn_multiplier
        )

        if leaf_features is not None:
            # store from White's perspective regardless of whose move it was
            history.append(dict(leaf_features))

        # actually pick and play a move (re-run a shallow search to choose
        # which move to make, mirroring SmartMoveFinder's structure)
        best_move = None
        best_score = -CHECKMATE - 1
        random.shuffle(valid_moves)
        alpha, beta = -CHECKMATE - 1, CHECKMATE + 1
        for move in valid_moves:
            gs.makeMove(move)
            next_moves = gs.getValidMoves()
            s, _ = negamax_leaf(gs, evaluator, depth - 1, -beta, -alpha, -turn_multiplier)
            s = -s
            gs.undoMove()
            if s > best_score:
                best_score = s
                best_move = move
            if best_score > alpha:
                alpha = best_score

        if best_move is None:
            break
        gs.makeMove(best_move)
        gs.getValidMoves()  # refreshes gs.checkmate / gs.stalemate flags

    # determine final outcome from White's perspective
    if gs.checkmate:
        outcome = -1.0 if gs.whiteToMove else 1.0
    else:
        outcome = 0.0  # stalemate / move-limit reached -> treat as draw

    return history, outcome


def td_update(evaluator, history, outcome, alpha_lr, td_clip=8.0):
    """Simplified TD(0)-on-leaf-values update (lambda = 0 case of TD-Leaf).

    For each ply t, the "target" is the next ply's leaf value (or the final
    game outcome for the last ply). The weights move in the direction that
    would have made evaluate(features_t) closer to that target.

    IMPORTANT: the terminal target is scaled to TERMINAL_TARGET (roughly
    the natural range of the linear material-based evaluation, ~40), NOT
    the search's CHECKMATE constant (1000) used for pruning. Mixing those
    two scales causes the weight updates to blow up after just a few games
    (this was caught by testing before handing this off - an earlier
    version used CHECKMATE directly here and the weights diverged wildly).
    td_error is also clipped to keep any single move from dominating the
    learned weights.

    SANITY FLOOR: material is mathematically certain to always matter
    positively in chess (more material is never bad, all else equal) and
    its correct relative values are already well-established (queen=9,
    rook=5, etc.) - there's nothing genuinely uncertain for RL to discover
    there. So material is EXCLUDED from learning entirely and stays fixed;
    only the positional features (mobility, center control, king safety,
    development) are tuned by self-play.

    This was a design change made after testing: an earlier version let
    material update like everything else, and over hundreds of depth-1
    self-play games it drifted toward negative values (i.e. the engine
    "learning" that losing pieces is good) because depth-1 self-play is
    too noisy a signal for something that isn't actually uncertain.
    """
    TERMINAL_TARGET = 40.0  # roughly the max plausible material imbalance
    LEARNED_FEATURES = [f for f in FEATURE_NAMES if f != "material"]

    weights = evaluator.weights
    values = [evaluator.evaluate_from_features(f) for f in history]
    targets = values[1:] + [outcome * TERMINAL_TARGET]

    for features, value, target in zip(history, values, targets):
        td_error = target - value
        td_error = max(-td_clip, min(td_clip, td_error))  # gradient clipping
        for name in LEARNED_FEATURES:
            weights[name] += alpha_lr * td_error * features[name]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--games", type=int, default=100)
    parser.add_argument("--depth", type=int, default=2,
                         help="Search depth during training (shallow = faster; default 2)")
    parser.add_argument("--alpha", type=float, default=0.0005,
                         help="Learning rate for weight updates")
    parser.add_argument("--save-every", type=int, default=10)
    args = parser.parse_args()

    evaluator = Evaluator()
    print("Starting weights:", evaluator.weights)

    for game_num in range(1, args.games + 1):
        history, outcome = play_one_game(evaluator, args.depth)
        td_update(evaluator, history, outcome, args.alpha)

        result_str = {1.0: "White wins", -1.0: "Black wins", 0.0: "Draw"}[outcome]
        print(f"Game {game_num}/{args.games} - {result_str} - "
              f"{len(history)} plies recorded")

        if game_num % args.save_every == 0:
            evaluator.save()
            print(f"  -> saved weights to {evaluator.weights_path}")
            print(f"  -> current weights: {evaluator.weights}")

    evaluator.save()
    print("\nFinal weights:", evaluator.weights)
    print(f"Saved to {evaluator.weights_path}")


if __name__ == "__main__":
    main()
