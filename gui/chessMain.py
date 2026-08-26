import pygame as p  # type: ignore
import sys
from pathlib import Path

# Add the parent directory to the path so we can import engine
sys.path.insert(0, str(Path(__file__).parent.parent))

from engine import chessEngine
from engine import SmartMoveFinder

p.init()
p.display.set_caption("Caïssa Chess")
icon = p.image.load("assets/logo.png")
p.display.set_icon(icon)

# Define colors for a cleaner aesthetic
LIGHT_SQUARE = "#F0D9B5"  # Soft beige
DARK_SQUARE = "#B58863"   # Warm brown
BG_COLOR = "#2C3E50"      # Dark blue-gray
HIGHLIGHT_COLOR = (170, 162, 58, 100)  # Golden yellow with transparency
LAST_MOVE_COLOR = (100, 111, 159, 120)  # Soft blue with transparency
TEXT_COLOR = "#ECF0F1"    # Off-white
BUTTON_COLOR = "#34495E"  # Darker blue-gray
BUTTON_HOVER = "#4A5C6B"  # Lighter when hovered
ACCENT_COLOR = "#3498DB"  # Bright blue for accents
RESIGN_BUTTON_COLOR = "#E74C3C"  # Red for resign button
RESIGN_BUTTON_HOVER = "#C0392B"  # Darker red when hovered


# Board dimensions
WIDTH = HEIGHT = 560
DIMENSION = 8
SQ_SIZE = HEIGHT // DIMENSION
MAX_FPS = 60  # Smoother animations

# Add padding around the board
PADDING = 40
WINDOW_WIDTH = WIDTH + PADDING * 2

# Button dimensions
BUTTON_WIDTH = 140
BUTTON_HEIGHT = 50
BUTTON_MARGIN = 20

# Bottom panel for buttons and status
PANEL_HEIGHT = 80
WINDOW_HEIGHT = HEIGHT + PADDING * 2 + PANEL_HEIGHT

# Global variables
IMAGES = {}
game_over = False
game_result = ""

# Player info panel dimensions
INFO_PANEL_WIDTH = 240
WINDOW_WIDTH = WIDTH + PADDING * 3 + INFO_PANEL_WIDTH

# Button dimensions for abort/resign
RESIGN_BUTTON_WIDTH = 120
RESIGN_BUTTON_HEIGHT = 40

# Additional global variables
captured_pieces_white = []
captured_pieces_black = []
player_names = {"White": "You", "Black": "Caïssa (AI)"}
game_aborted = False


def loadImages():
    pieces = ['Wk', 'Wq', 'Wr', 'Wb', 'Wn',
              'Wp', 'Bk', 'Bq', 'Br', 'Bn', 'Bb', 'Bp']
    for piece in pieces:
        IMAGES[piece] = p.transform.scale(
            p.image.load("assets/pieces/" + piece + ".png"), (SQ_SIZE, SQ_SIZE)
        )

# Check if mouse is over a button


def is_over_button(pos, button_rect):
    return button_rect.collidepoint(pos)

# Draw a button with hover effect


def draw_button(screen, rect, text, font, hover=False):
    color = BUTTON_HOVER if hover else BUTTON_COLOR
    p.draw.rect(screen, p.Color(color), rect, border_radius=5)
    # Add a slight 3D effect with a bottom border
    p.draw.line(screen, p.Color(BG_COLOR),
                (rect.left, rect.bottom-1),
                (rect.right, rect.bottom-1), 2)
    text_surf = font.render(text, True, p.Color(TEXT_COLOR))
    text_rect = text_surf.get_rect(center=rect.center)
    screen.blit(text_surf, text_rect)


def main():
    global game_over, game_result, game_aborted

    screen = p.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock = p.time.Clock()

    info_font = p.font.SysFont("Segoe UI", 16)
    player_font = p.font.SysFont("Segoe UI", 20, bold=True)
    button_font = p.font.SysFont("Segoe UI", 16, bold=True)
    result_font = p.font.SysFont("Segoe UI", 24, bold=True)

    # Initialize game state
    gs = chessEngine.GameState()
    validMoves = gs.getValidMoves()
    moveMade = False
    isUndo = False
    loadImages()
    running = True
    sqSelected = ()
    playerClicks = []
    playerOne = True  # if human is playing white, then this will be True, If an AI is Playing then it will be false
    playerTwo = False  # same as above but for black

    # Position resign button in a more visible spot like chess.com
    resign_button = p.Rect(
        WINDOW_WIDTH//2 + BUTTON_WIDTH + BUTTON_MARGIN * 3//2,
        HEIGHT + PADDING * 2 + PANEL_HEIGHT//2 - RESIGN_BUTTON_HEIGHT//2,
        RESIGN_BUTTON_WIDTH,
        RESIGN_BUTTON_HEIGHT
    )

    # Create button rectangles
    reset_button = p.Rect(
        WINDOW_WIDTH//2 - BUTTON_WIDTH - BUTTON_MARGIN//2,
        HEIGHT + PADDING * 2 + PANEL_HEIGHT//2 - BUTTON_HEIGHT//2,
        BUTTON_WIDTH,
        BUTTON_HEIGHT
    )

    undo_button = p.Rect(
        WINDOW_WIDTH//2 + BUTTON_MARGIN//2,
        HEIGHT + PADDING * 2 + PANEL_HEIGHT//2 - BUTTON_HEIGHT//2,
        BUTTON_WIDTH,
        BUTTON_HEIGHT
    )

    # Track button hover states
    reset_hover = False
    undo_hover = False
    resign_hover = False

    # Function to reset the game
    def resetGame():
        nonlocal gs, validMoves, moveMade, sqSelected, playerClicks
        global game_over, game_result
        gs = chessEngine.GameState()
        validMoves = gs.getValidMoves()
        moveMade = False
        sqSelected = ()
        playerClicks = []
        game_over = False
        game_result = ""

    def drawInfoPanel(screen, gs, player_font, info_font):
        # Panel background
        panel_rect = p.Rect(WIDTH + PADDING * 2, PADDING,
                            INFO_PANEL_WIDTH, HEIGHT)
        p.draw.rect(screen, p.Color(BG_COLOR), panel_rect)
        p.draw.rect(screen, p.Color(ACCENT_COLOR),
                    panel_rect, 2, border_radius=3)

        # Player names
        white_name_y = HEIGHT - PADDING - 100
        black_name_y = PADDING + 20

        # White player section (bottom)
        white_section = p.Rect(WIDTH + PADDING * 2 + 10, white_name_y - 10,
                               INFO_PANEL_WIDTH - 20, 50)
        p.draw.rect(screen, p.Color("#2E4053"), white_section, border_radius=5)

        white_name_text = player_font.render(
            player_names["White"], True, p.Color(TEXT_COLOR))
        screen.blit(white_name_text, (WIDTH + PADDING * 2 + 20, white_name_y))

        # Black player section (top)
        black_section = p.Rect(WIDTH + PADDING * 2 + 10, black_name_y - 10,
                               INFO_PANEL_WIDTH - 20, 50)
        p.draw.rect(screen, p.Color("#2E4053"), black_section, border_radius=5)

        black_name_text = player_font.render(
            player_names["Black"], True, p.Color(TEXT_COLOR))
        screen.blit(black_name_text, (WIDTH + PADDING * 2 + 20, black_name_y))

        # Indicate active player
        active_y = black_name_y if not gs.whiteToMove else white_name_y
        active_section = black_section if not gs.whiteToMove else white_section
        p.draw.rect(screen, p.Color(ACCENT_COLOR),
                    active_section, 2, border_radius=5)
        p.draw.circle(screen, p.Color(ACCENT_COLOR),
                      (WIDTH + PADDING * 2 + 10, active_y + 10), 5)

        # Draw captured pieces
        drawCapturedPieces(screen, gs, info_font)

        # Draw Evaluation Bar
        drawEvaluationBar(screen, gs)

    def drawCapturedPieces(screen, gs, font):
        piece_size = SQ_SIZE // 2.5
        x_start = WIDTH + PADDING * 2 + 20
        captured_spacing = piece_size + 8

        # Material count trackers
        white_captured_material = 0
        black_captured_material = 0

        piece_values = {'p': 1, 'n': 3, 'b': 3, 'r': 5, 'q': 9}

        # --- BLACK captures WHITE pieces (displayed at top) ---
        black_captures_label_y = PADDING + 90
        black_captures_y = black_captures_label_y + 25

        black_captures_text = font.render(
            "Captured:", True, p.Color(TEXT_COLOR))
        screen.blit(black_captures_text, (x_start, black_captures_label_y))

        if 'W' in gs.capturedPieces:
            piece_counts = {'p': 0, 'n': 0, 'b': 0, 'r': 0, 'q': 0}
            for piece in gs.capturedPieces['W']:
                piece_counts[piece.lower()] += 1
                white_captured_material += piece_values[piece.lower()]

            x_offset = 0
            for piece_type in ['p', 'n', 'b', 'r', 'q']:
                count = piece_counts[piece_type]
                if count > 0:
                    piece_key = f'W{piece_type}'
                    scaled_image = p.transform.scale(
                        IMAGES[piece_key], (piece_size, piece_size))
                    screen.blit(scaled_image, (x_start +
                                x_offset, black_captures_y))

                    if count > 1:
                        count_text = font.render(
                            f"x{count}", True, p.Color(TEXT_COLOR))
                        screen.blit(count_text, (x_start + x_offset +
                                    piece_size - 5, black_captures_y + piece_size - 15))

                    x_offset += captured_spacing

        # --- WHITE captures BLACK pieces (displayed at bottom) ---
        white_captures_label_y = HEIGHT - PADDING - 190
        white_captures_y = white_captures_label_y + 25

        white_captures_text = font.render(
            "Captured:", True, p.Color(TEXT_COLOR))
        screen.blit(white_captures_text, (x_start, white_captures_label_y))

        if 'B' in gs.capturedPieces:
            piece_counts = {'p': 0, 'n': 0, 'b': 0, 'r': 0, 'q': 0}
            for piece in gs.capturedPieces['B']:
                piece_counts[piece.lower()] += 1
                black_captured_material += piece_values[piece.lower()]

            x_offset = 0
            for piece_type in ['p', 'n', 'b', 'r', 'q']:
                count = piece_counts[piece_type]
                if count > 0:
                    piece_key = f'B{piece_type}'
                    scaled_image = p.transform.scale(
                        IMAGES[piece_key], (piece_size, piece_size))
                    screen.blit(scaled_image, (x_start +
                                x_offset, white_captures_y))

                    if count > 1:
                        count_text = font.render(
                            f"x{count}", True, p.Color(TEXT_COLOR))
                        screen.blit(count_text, (x_start + x_offset +
                                    piece_size - 5, white_captures_y + piece_size - 15))

                    x_offset += captured_spacing

        # --- Show material advantage if any ---
        # Black's material advantage
        material_diff = white_captured_material - black_captured_material
        if material_diff > 0:
            adv_text = font.render(
                f"+{material_diff}", True, p.Color("#FFFFFF"))
            screen.blit(adv_text, (WIDTH + PADDING * 2 +
                        INFO_PANEL_WIDTH - 50, black_captures_label_y))
        elif material_diff < 0:
            adv_text = font.render(
                f"+{abs(material_diff)}", True, p.Color("#FFFFFF"))
            screen.blit(adv_text, (WIDTH + PADDING * 2 +
                        INFO_PANEL_WIDTH - 50, white_captures_label_y))

    def drawEvaluationBar(screen, gs):
        """Draws a professional horizontal evaluation bar that updates dynamically."""
        bar_x = WIDTH + PADDING * 2 + 20
        bar_y = HEIGHT // 2 - 20
        bar_width = INFO_PANEL_WIDTH - 40
        bar_height = 20

        # Draw border
        p.draw.rect(screen, p.Color(ACCENT_COLOR), (bar_x, bar_y,
                    bar_width, bar_height), 2, border_radius=5)

        # Calculate score
        material_score = calculateMaterialScore(gs)
        max_score = 30  # Adjust if needed

        # Normalize material score from -max_score...0...+max_score to 0...1
        percent = (material_score + max_score) / (2 * max_score)
        percent = max(0, min(1, percent))  # clamp

        # White part width
        white_width = int(bar_width * percent)
        black_width = bar_width - white_width

        # Draw white side
        if white_width > 0:
            p.draw.rect(screen, p.Color("#ECF0F1"), (bar_x, bar_y,
                        white_width, bar_height), border_radius=5)

        # Draw black side
        if black_width > 0:
            p.draw.rect(screen, p.Color("black"), (bar_x + white_width,
                        bar_y, black_width, bar_height), border_radius=5)

    def calculateMaterialScore(gs):
        """Calculate material score (positive = white advantage, negative = black advantage)"""
        score = 0
        piece_values = {'p': 1, 'n': 3, 'b': 3, 'r': 5, 'q': 9, 'k': 0}

        for row in gs.board:
            for square in row:
                if square != '--':
                    color, piece_type = square[0], square[1].lower()
                    if color == 'W':
                        score += piece_values[piece_type]
                    else:
                        score -= piece_values[piece_type]

        return score

    while running:
        mouse_pos = p.mouse.get_pos()

        # Update button hover states
        reset_hover = is_over_button(mouse_pos, reset_button)
        undo_hover = is_over_button(mouse_pos, undo_button)
        resign_hover = is_over_button(mouse_pos, resign_button)
        humanTurn = (gs.whiteToMove and playerOne) or (
            not gs.whiteToMove and playerTwo)

        for e in p.event.get():
            if e.type == p.QUIT:
                running = False

            # Mouse handler
            elif e.type == p.MOUSEBUTTONDOWN:
                location = p.mouse.get_pos()

                # Check if reset button was clicked
                if is_over_button(location, reset_button):
                    resetGame()
                    continue

                # Check if undo button was clicked
                if is_over_button(location, undo_button) and len(gs.moveLog) > 0:
                    gs.undoMove()
                    moveMade = True
                    isUndo = True
                    game_over = False
                    game_result = ""
                    continue

                # check if abort button was clicked
                if is_over_button(location, resign_button) and not game_over:
                    game_over = True
                    game_aborted = True
                    if gs.whiteToMove:
                        game_result = "Black wins by resignation"
                    else:
                        game_result = "White wins by resignation"
                    continue
                # Process board clicks only if game is not over
                if not game_over and humanTurn:
                    # Adjust for padding to get board coordinates
                    board_x = location[0] - PADDING
                    board_y = location[1] - PADDING

                    # Check if click is within the board
                    if 0 <= board_x < WIDTH and 0 <= board_y < HEIGHT:
                        col = board_x // SQ_SIZE
                        row = board_y // SQ_SIZE

                        if sqSelected == (row, col):  # Clicked same square twice
                            sqSelected = ()
                            playerClicks = []
                        else:
                            sqSelected = (row, col)
                            playerClicks.append(sqSelected)

                        if len(playerClicks) == 2:  # After 2nd click
                            move = chessEngine.Move(
                                playerClicks[0], playerClicks[1], gs.board)

                            for i in range(len(validMoves)):
                                if move == validMoves[i]:
                                    gs.makeMove(validMoves[i])
                                    moveMade = True
                                    isUndo = False
                                    sqSelected = ()
                                    playerClicks = []

                            if not moveMade:
                                playerClicks = [sqSelected]

            # Key handlers (keeping Z as keyboard shortcut for undo)
            elif e.type == p.KEYDOWN and e.key == p.K_z and len(gs.moveLog) > 0:
                gs.undoMove()
                moveMade = True
                isUndo = True
                game_over = False
                game_result = ""

        # AI move finder logic
        if not game_over and not humanTurn:
            AIMove = SmartMoveFinder.findBestMoveNegaMax(gs, validMoves)
            if AIMove is None:
                AIMove = SmartMoveFinder.findRandomMove(validMoves)
            gs.makeMove(AIMove)
            moveMade = True

        if moveMade:
            if not isUndo and len(gs.moveLog) > 0:
                animateMove(gs.moveLog[-1], screen, gs.board, clock)
            validMoves = gs.getValidMoves()
            moveMade = False
            isUndo = False

            # Check for game end conditions
            if gs.checkmate:
                game_over = True
                if gs.whiteToMove:
                    game_result = "Black Wins by Checkmate"
                else:
                    game_result = "White Wins by Checkmate"
            elif gs.stalemate:
                game_over = True
                game_result = "Draw by Stalemate"

        # Draw everything
        screen.fill(p.Color(BG_COLOR))

        # Draw board with padding
        drawGameState(screen, gs, validMoves, sqSelected)

        # Draw buttons
        draw_button(screen, reset_button, "New Game", button_font, reset_hover)
        draw_button(screen, undo_button, "Undo Move", button_font, undo_hover)

        # Display turn indicator
        turn_text = "White to Move" if gs.whiteToMove else "Black to Move"
        turn_surf = button_font.render(turn_text, True, p.Color(TEXT_COLOR))
        turn_rect = turn_surf.get_rect(
            center=(WINDOW_WIDTH//2, HEIGHT + PADDING + 20))
        screen.blit(turn_surf, turn_rect)

        # Draw info panel
        drawInfoPanel(screen, gs, player_font, info_font)

        # Draw abort/resign button
        if not game_over:
            button_text = "Resign" if len(gs.moveLog) > 2 else "Abort"
            # Use red color for resign button
            resign_color = RESIGN_BUTTON_HOVER if resign_hover else RESIGN_BUTTON_COLOR
            p.draw.rect(screen, p.Color(resign_color),
                        resign_button, border_radius=5)
            resign_text = button_font.render(
                button_text, True, p.Color(TEXT_COLOR))
            resign_rect = resign_text.get_rect(center=resign_button.center)
            screen.blit(resign_text, resign_rect)

        # Display game result if game is over
        if game_over:

            if gs.stalemate and hasattr(gs, 'drawReason') and gs.drawReason:
                game_result = f"Draw by {gs.drawReason}"
            # Create semi-transparent overlay for game over message
            overlay = p.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(180)
            overlay.fill(p.Color(BG_COLOR))
            screen.blit(overlay, (PADDING, PADDING))

            result_surf = result_font.render(
                game_result, True, p.Color(TEXT_COLOR))

            # CENTER relative only to board
            result_rect = result_surf.get_rect(
                center=(PADDING + WIDTH // 2, PADDING + HEIGHT // 2 - 20))
            screen.blit(result_surf, result_rect)

            # Add prompt text
            prompt_surf = button_font.render(
                "Click 'New Game' to play again", True, p.Color(TEXT_COLOR))
            prompt_rect = prompt_surf.get_rect(
                center=(PADDING + WIDTH // 2, PADDING + HEIGHT // 2 + 20))
            screen.blit(prompt_surf, prompt_rect)

        p.display.flip()
        clock.tick(MAX_FPS)


def highlightSquares(screen, gs, validMoves, sqSelected):
    # Highlight last move
    if gs.moveLog:
        lastMove = gs.moveLog[-1]
        last_move_s = p.Surface((SQ_SIZE, SQ_SIZE))
        last_move_s.fill(p.Color(LAST_MOVE_COLOR))

        # Highlight both squares of last move
        screen.blit(last_move_s, (PADDING + lastMove.startCol *
                    SQ_SIZE, PADDING + lastMove.startRow*SQ_SIZE))
        screen.blit(last_move_s, (PADDING + lastMove.endCol *
                    SQ_SIZE, PADDING + lastMove.endRow*SQ_SIZE))

    # Highlight selected square and valid moves
    if sqSelected != ():
        r, c = sqSelected

        # Check if the selected piece belongs to the current player
        if gs.board[r][c][0] == ('W' if gs.whiteToMove else 'B'):
            # Create highlighting surface
            s = p.Surface((SQ_SIZE, SQ_SIZE))
            s.set_alpha(100)
            s.fill(p.Color(HIGHLIGHT_COLOR))

            # Highlight selected square
            screen.blit(s, (PADDING + c*SQ_SIZE, PADDING + r*SQ_SIZE))

            # Highlight valid moves from that square with subtle circles
            for move in validMoves:
                if move.startRow == r and move.startCol == c:
                    if gs.board[move.endRow][move.endCol] == '--':
                        # Empty square - draw circle
                        radius = SQ_SIZE // 6
                        center = (PADDING + move.endCol*SQ_SIZE + SQ_SIZE//2,
                                  PADDING + move.endRow*SQ_SIZE + SQ_SIZE//2)
                        p.draw.circle(screen, p.Color(
                            HIGHLIGHT_COLOR), center, radius)
                    else:
                        # Capture square - draw ring
                        s.set_alpha(180)
                        screen.blit(s, (PADDING + move.endCol *
                                    SQ_SIZE, PADDING + move.endRow*SQ_SIZE))
                        inner = p.Surface((SQ_SIZE*0.8, SQ_SIZE*0.8))
                        inner.fill(
                            p.Color(colors[(move.endRow + move.endCol) % 2]))
                        inner_pos = (PADDING + move.endCol*SQ_SIZE + SQ_SIZE*0.1,
                                     PADDING + move.endRow*SQ_SIZE + SQ_SIZE*0.1)
                        screen.blit(inner, inner_pos)


def drawGameState(screen, gs, validMoves, sqSelected):
    drawBoard(screen)
    highlightSquares(screen, gs, validMoves, sqSelected)
    drawPieces(screen, gs.board)

    # Draw border around the board
    border_rect = p.Rect(PADDING-2, PADDING-2, WIDTH+4, HEIGHT+4)
    p.draw.rect(screen, p.Color(ACCENT_COLOR), border_rect, 2, border_radius=3)


def drawBoard(screen):
    global colors
    colors = [p.Color(LIGHT_SQUARE), p.Color(DARK_SQUARE)]

    for r in range(DIMENSION):
        for c in range(DIMENSION):
            color = colors[(r + c) % 2]
            p.draw.rect(screen, color, p.Rect(
                PADDING + c * SQ_SIZE, PADDING + r * SQ_SIZE, SQ_SIZE, SQ_SIZE))

            # Optional: Add subtle rank/file notation
            if r == 7:  # Bottom rank
                if (r + c) % 2 == 0:
                    text_color = p.Color(DARK_SQUARE)
                else:
                    text_color = p.Color(LIGHT_SQUARE)

                file_font = p.font.SysFont("Segoe UI", 12)
                file_text = file_font.render(
                    chr(ord('a') + c), True, text_color)
                screen.blit(file_text, (PADDING + c *
                            SQ_SIZE + 5, PADDING + HEIGHT - 15))

            if c == 0:  # Left file
                if (r + c) % 2 == 0:
                    text_color = p.Color(DARK_SQUARE)
                else:
                    text_color = p.Color(LIGHT_SQUARE)

                rank_font = p.font.SysFont("Segoe UI", 12)
                rank_text = rank_font.render(str(8-r), True, text_color)
                screen.blit(rank_text, (PADDING + 5,
                            PADDING + r * SQ_SIZE + 5))


def drawPieces(screen, board):
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            piece = board[r][c]
            if piece != "--":
                screen.blit(IMAGES[piece], p.Rect(
                    PADDING + c * SQ_SIZE, PADDING + r * SQ_SIZE, SQ_SIZE, SQ_SIZE))


def animateMove(move, screen, board, clock):
    """Animates a chess piece moving from start to end position with smooth motion"""
    global colors
    dR = move.endRow - move.startRow
    dC = move.endCol - move.startCol

    # Optimize animation speed and smoothness
    fps = 60  # Target fps for smooth animation
    duration = 0.2  # Animation duration in seconds
    frameCount = int(fps * duration)

    # Get the moving piece
    movingPiece = move.pieceMoved

    # Create a copy of the board for animation
    tempBoard = [row[:] for row in board]
    # Temporarily remove the piece from the board
    tempBoard[move.startRow][move.startCol] = "--"

    # Pre-render the static board background once
    staticBG = p.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
    staticBG.fill(p.Color(BG_COLOR))
    drawBoard(staticBG)

    # Draw border around the board
    border_rect = p.Rect(PADDING-2, PADDING-2, WIDTH+4, HEIGHT+4)
    p.draw.rect(staticBG, p.Color(ACCENT_COLOR),
                border_rect, 2, border_radius=3)

    # Draw all non-moving pieces on the static background
    for row in range(DIMENSION):
        for col in range(DIMENSION):
            piece = tempBoard[row][col]
            if piece != "--":
                staticBG.blit(IMAGES[piece], p.Rect(
                    PADDING + col * SQ_SIZE, PADDING + row * SQ_SIZE, SQ_SIZE, SQ_SIZE))

    # Calculate the step size for smooth motion
    stepR = dR / frameCount if frameCount > 0 else dR
    stepC = dC / frameCount if frameCount > 0 else dC

    # Animation loop
    for frame in range(frameCount + 1):
        # Calculate the position for this frame using float for smoother interpolation
        r = move.startRow + stepR * frame
        c = move.startCol + stepC * frame

        # Draw the static background (includes board and non-moving pieces)
        screen.blit(staticBG, (0, 0))

        # Draw the moving piece at its current position
        screen.blit(IMAGES[movingPiece], p.Rect(
            PADDING + c * SQ_SIZE, PADDING + r * SQ_SIZE, SQ_SIZE, SQ_SIZE))

        # Update the display and maintain framerate
        p.display.update()
        clock.tick(fps)


if __name__ == "__main__":
    main()
