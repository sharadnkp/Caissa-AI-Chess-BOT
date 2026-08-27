"""
evaluation.py

A weighted-feature evaluation function for Caissa, designed to be tuned by
reinforcement learning (TD-Leaf) instead of hand-picked by guessing.

Instead of just adding up piece values, the position is scored as a weighted
sum of several features. Learning tunes the WEIGHTS; the features themselves
stay fixed (this is exactly how classic engines like KnightCap improved via
TD-Leaf self-play before neural-network evaluation existed).

Usage:
    from engine.evaluation import Evaluator
    ev = Evaluator()                 # loads learned weights if present,
                                      # otherwise starts from sane defaults
    score = ev.evaluate(gs)          # positive = good for White
    features = ev.extract_features(gs)  # raw feature vector, used by training
"""
import json
import os

PIECE_VALUES = {"k": 0, "q": 9, "r": 5, "b": 3, "n": 3, "p": 1}

# The central 4 squares are the most valuable to control; the next ring
# a bit less so. This mirrors classic chess heuristics.
CENTER_SQUARES = {(3, 3), (3, 4), (4, 3), (4, 4)}
EXTENDED_CENTER = {
    (r, c) for r in range(2, 6) for c in range(2, 6)
} - CENTER_SQUARES

FEATURE_NAMES = [
    "material",        # sum of piece values, White minus Black
    "mobility",        # (num legal moves available to side to move) sign-adjusted
    "center_control",  # pieces occupying/attacking the central 4 squares
    "extended_center",  # pieces occupying the wider center ring
    "king_safety",     # simple pawn-shield heuristic near each king
    "development",     # knights/bishops moved off the back rank
]

DEFAULT_WEIGHTS = {
    "material": 1.0,
    "mobility": 0.02,
    "center_control": 0.10,
    "extended_center": 0.03,
    "king_safety": 0.05,
    "development": 0.05,
}

WEIGHTS_PATH = os.path.join(os.path.dirname(__file__), "learned_weights.json")


class Evaluator:
    def __init__(self, weights_path=WEIGHTS_PATH):
        self.weights_path = weights_path
        self.weights = dict(DEFAULT_WEIGHTS)
        self.load()

    def load(self):
        if os.path.exists(self.weights_path):
            with open(self.weights_path) as f:
                saved = json.load(f)
            self.weights.update(saved)

    def save(self):
        with open(self.weights_path, "w") as f:
            json.dump(self.weights, f, indent=2)

    def weight_vector(self):
        return [self.weights[name] for name in FEATURE_NAMES]

    def set_weight_vector(self, vec):
        for name, val in zip(FEATURE_NAMES, vec):
            self.weights[name] = val

    # ---- feature extraction -------------------------------------------------

    def extract_features(self, gs):
        """Returns a dict of raw feature values (before weighting).
        All features are computed as White-minus-Black, so a positive
        feature value means it favors White.
        """
        board = gs.board
        material = 0
        development = 0
        center_control = 0
        extended_center = 0

        for r in range(8):
            for c in range(8):
                sq = board[r][c]
                if sq == "--":
                    continue
                color, piece = sq[0], sq[1].lower()
                sign = 1 if color == "W" else -1

                material += sign * PIECE_VALUES[piece]

                if (r, c) in CENTER_SQUARES:
                    center_control += sign
                elif (r, c) in EXTENDED_CENTER:
                    extended_center += sign

                # crude development heuristic: knights/bishops not on their
                # starting back-rank squares count as "developed"
                if piece in ("n", "b"):
                    back_row = 0 if color == "B" else 7
                    if r != back_row:
                        development += sign

        # mobility: how many legal moves does the side to move have, relative
        # to a rough "average" - we sign it so it's White-minus-Black by
        # temporarily counting for both sides using pseudo-legal move counts
        # (cheap approximation: count getAllPossibleMoves for both colors)
        mobility = self._mobility_diff(gs)

        king_safety = self._king_safety_diff(gs)

        return {
            "material": material,
            "mobility": mobility,
            "center_control": center_control,
            "extended_center": extended_center,
            "king_safety": king_safety,
            "development": development,
        }

    def _mobility_diff(self, gs):
        """Cheap mobility estimate: count pseudo-legal moves for both sides
        without full legality (check) filtering, since that's expensive to
        do twice per node. Good enough as a learned-weight feature.
        """
        original_turn = gs.whiteToMove

        gs.whiteToMove = True
        white_moves = len(gs.getAllPossibleMoves())

        gs.whiteToMove = False
        black_moves = len(gs.getAllPossibleMoves())

        gs.whiteToMove = original_turn
        return white_moves - black_moves

    def _king_safety_diff(self, gs):
        """Very simple pawn-shield heuristic: count friendly pawns in the
        3 squares directly in front of each king. More shield pawns = safer.
        """
        def shield_count(king_pos, color):
            r, c = king_pos
            direction = -1 if color == "W" else 1
            shield_row = r + direction
            if not (0 <= shield_row < 8):
                return 0
            count = 0
            for cc in (c - 1, c, c + 1):
                if 0 <= cc < 8 and gs.board[shield_row][cc] == color + "p":
                    count += 1
            return count

        white_safety = shield_count(gs.WhiteKingLocation, "W")
        black_safety = shield_count(gs.BlackKingLocation, "B")
        return white_safety - black_safety

    # ---- scoring --------------------------------------------------------

    def evaluate(self, gs, CHECKMATE=1000, STALEMATE=0):
        if gs.checkmate:
            return -CHECKMATE if gs.whiteToMove else CHECKMATE
        if gs.stalemate:
            return STALEMATE

        features = self.extract_features(gs)
        score = sum(self.weights[name] * features[name] for name in FEATURE_NAMES)
        return score

    def evaluate_from_features(self, features):
        """Score directly from an already-extracted feature dict - used by
        the training loop to avoid recomputing features twice."""
        return sum(self.weights[name] * features[name] for name in FEATURE_NAMES)
