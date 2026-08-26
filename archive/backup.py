import pygame as p  # type: ignore
import chessEngine

p.init()
p.display.set_caption("Caïssa Chess")  # Change window title
# Example: using the white king as the icon
icon = p.image.load("logo.png")
p.display.set_icon(icon)

WIDTH = HEIGHT = 512

DIMENSION = 8
SQ_SIZE = HEIGHT // DIMENSION
MAX_FPS = 15
IMAGES = {}

# global initialization of the images in the main once


def loadImages():
    pieces = ['Wk', 'Wq', 'Wr', 'Wb', 'Wn',
              'Wp', 'Bk', 'Bq', 'Br', 'Bn', 'Bb', 'Bp']
    for piece in pieces:
        IMAGES[piece] = p.transform.scale(
            p.image.load("pieces/" + piece + ".png"), (SQ_SIZE, SQ_SIZE)
        )

# this is the main driver code of our program, it'll handle the input and updating the graphics


def main():
    screen = p.display.set_mode((WIDTH, HEIGHT))
    clock = p.time.Clock()
    screen.fill(p.Color("white"))
    gs = chessEngine.GameState()
    validMoves = gs.getValidMoves()
    moveMade = False  # flag var for when a move is made
    isUndo = False    # new flag to track undo operations
    loadImages()      # only do this once, before the while loop
    running = True
    sqSelected = ()   # no square seleceted rn
    playerClicks = []  # keep track of player clicks

    while running:
        for e in p.event.get():
            if e.type == p.QUIT:
                running = False
            # mouse handler
            elif e.type == p.MOUSEBUTTONDOWN:
                location = p.mouse.get_pos()  # gets the (x,y) location of mouse
                col = location[0]//SQ_SIZE
                row = location[1]//SQ_SIZE
                if sqSelected == (row, col):  # the user clicked the same square twice
                    sqSelected = ()  # deselect
                    playerClicks = []  # clear players click
                else:
                    sqSelected = (row, col)
                    # append for both 1st and 2nd clicks
                    playerClicks.append(sqSelected)
                if len(playerClicks) == 2:  # after 2nd click
                    move = chessEngine.Move(
                        playerClicks[0], playerClicks[1], gs.board)
                    print(move.getChessNotation())
                    for i in range(len(validMoves)):
                        if move == validMoves[i]:
                            gs.makeMove(validMoves[i])
                            moveMade = True
                            isUndo = False  # This is a regular move, not an undo
                            sqSelected = ()  # reset user clicks
                            playerClicks = []
                    if not moveMade:
                        playerClicks = [sqSelected]
            # key handlers
            elif e.type == p.KEYDOWN and e.key == p.K_z:  # undo when 'z' is pressed
                gs.undoMove()
                moveMade = True
                isUndo = True  # Flag this as an undo operation

        if moveMade:
            if not isUndo and len(gs.moveLog) > 0:  # Only animate if not an undo
                animateMove(gs.moveLog[-1], screen, gs.board, clock)
            validMoves = gs.getValidMoves()
            moveMade = False
            isUndo = False  # Reset the undo flag

        # Call this function to draw the board
        drawGameState(screen, gs, validMoves, sqSelected)
        clock.tick(MAX_FPS)
        p.display.flip()


# Highlights the square selected and moves for the pices selected

def highlightSquares(screen, gs, validMoves, sqSelected):
    # Create a new surface for highlights
    s = p.Surface((SQ_SIZE, SQ_SIZE))
    s.set_alpha(100)  # Transparency value

    # Highlight last move first (so it appears underneath other highlights)
    if gs.moveLog:  # Check if moveLog is not empty
        lastMove = gs.moveLog[-1]
        # Use a distinct color for last move highlight
        s.fill(p.Color('blue'))
        # Highlight start square
        screen.blit(s, (lastMove.startCol*SQ_SIZE, lastMove.startRow*SQ_SIZE))
        # Highlight end square
        screen.blit(s, (lastMove.endCol*SQ_SIZE, lastMove.endRow*SQ_SIZE))

    # Then highlight the selected square and valid moves
    if sqSelected != ():
        r, c = sqSelected
        # Check if the selected piece belongs to the current player
        if gs.board[r][c][0] == ('W' if gs.whiteToMove else 'B'):
            # Highlight selected square
            s.fill(p.Color('gray'))
            screen.blit(s, (c*SQ_SIZE, r*SQ_SIZE))

            # Highlight possible moves from that square
            s.fill(p.Color('yellow'))
            for move in validMoves:
                if move.startRow == r and move.startCol == c:
                    screen.blit(s, (move.endCol*SQ_SIZE, move.endRow*SQ_SIZE))
# Responsible for all the graphics within current game state


def drawGameState(screen, gs, validMoves, sqSelected):
    drawBoard(screen)  # Draw squares on the board
    highlightSquares(screen, gs, validMoves, sqSelected)
    drawPieces(screen, gs.board)  # Draw pieces on top of the squares

# Draw squares on the board


def drawBoard(screen):
    global colors
    colors = [p.Color("#EBEBD0"), p.Color("#769454")]
    for r in range(DIMENSION):  # Fixed the incorrect range syntax
        for c in range(DIMENSION):
            color = colors[(r + c) % 2]
            p.draw.rect(screen, color, p.Rect(
                c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))


def drawPieces(screen, board):
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            piece = board[r][c]
            if piece != "--":
                screen.blit(IMAGES[piece], p.Rect(
                    c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))

# animating a move


def animateMove(move, screen, board, clock):
    global colors
    dR = move.endRow - move.startRow
    dC = move.endCol - move.startCol
    framesPerSquare = 10  # frmanes to move one square
    frameCount = (abs(dR) + abs(dC)) + framesPerSquare
    for frame in range(frameCount + 1):
        r, c = (move.startRow + dR*frame /
                frameCount, move.startCol + dC*frame/frameCount)
        drawBoard(screen)
        drawPieces(screen, board)
        # erase the piece moved from its ending square
        color = colors[(move.endRow + move.endCol) % 2]
        endSquare = p.Rect(move.endCol*SQ_SIZE,
                           move.endRow*SQ_SIZE, SQ_SIZE, SQ_SIZE)
        p.draw.rect(screen, color, endSquare)
        # draw captured piece onto rectangle
        if move.pieceCaptured != '--':
            screen.blit(IMAGES[move.pieceCaptured], endSquare)
        # draw moving piece
        screen.blit(IMAGES[move.pieceMoved], p.Rect(
            c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))
        p.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    main()
