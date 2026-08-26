# board design (B - Black, W - White) (p - pawn, r - rook, n - knight, q - queen, k - king)
class GameState:
    def __init__(self):
        self.board = [
            ["Br", "Bn", "Bb", "Bq", "Bk", "Bb", "Bn", "Br"],
            ["Bp", "Bp", "Bp", "Bp", "Bp", "Bp", "Bp", "Bp"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["Wp", "Wp", "Wp", "Wp", "Wp", "Wp", "Wp", "Wp"],
            ["Wr", "Wn", "Wb", "Wq", "Wk", "Wb", "Wn", "Wr"]
        ]
        self.MoveFunc = {'p':
                         self.getPawnMoves, 'r':
                         self.getRookMoves, 'b':
                         self.getBishopMoves, 'n':
                         self.getKnightMoves, 'k':
                         self.getKingMoves, 'q': self.getQueenMoves}
        self.whiteToMove = True
        self.moveLog = []
        self.WhiteKingLocation = (7, 4)
        self.BlackKingLocation = (0, 4)
        self.checkmate = False
        self.stalemate = False
        # co-ordinates for the square where en-passant is possible
        self.enpassantPossible = ()
        # castling
        self.currentCastlingRight = CastleRights(True, True, True, True)
        self.castleRightsLog = [CastleRights(
            self.currentCastlingRight.wks, self.currentCastlingRight.bks,  self.currentCastlingRight.wqs, self.currentCastlingRight.bqs)]
        self.fiftyMoveRule = 0  # Counter for the fifty-move rule
        self.positionLog = []  # Log positions for threefold repetition check
        self.capturedPieces = {'W': [], 'B': []}  # Track captured pieces
        self.saveCurrentPosition()  # Save initial position
    # takes a move asa parameter and executes it (it won't work for pawn promotion and en-passant or castling)

    def makeMove(self, move):
        piece_captured = self.board[move.endRow][move.endCol]
        pawn_moved = move.pieceMoved[1] == 'p'
        self.board[move.startRow][move.startCol] = "--"
        self.board[move.endRow][move.endCol] = move.pieceMoved
        self.moveLog.append(move)  # log the move so we can undo it later
        self.whiteToMove = not self.whiteToMove  # switch turn

        # if white king moved
        if move.pieceMoved == 'Wk':
            self.WhiteKingLocation = (move.endRow, move.endCol)
        # if black king moved
        elif move.pieceMoved == 'Bk':
            self.BlackKingLocation = (move.endRow, move.endCol)

        # Pawn Promotion
        if move.isPawnPromotion:
            self.board[move.endRow][move.endCol] = move.pieceMoved[0] + 'q'

        # En-passant capture (remove the opponent's pawn)
        if move.isEnpassantMove:
            # Determine the row of the captured pawn based on the current turn
            captured_pawn_row = move.endRow + 1 if not self.whiteToMove else move.endRow - 1
            self.board[captured_pawn_row][move.endCol] = '--'

        # update enpassantPossible variable
        # Only on 2 square pawn advances
        if move.pieceMoved[1] == 'p' and abs(move.startRow - move.endRow) == 2:
            self.enpassantPossible = (
                (move.startRow + move.endRow) // 2, move.startCol)
        else:
            self.enpassantPossible = ()

        # Castle Move
        if move.isCastleMove:
            if move.endCol - move.startCol == 2:  # kingside castle move
                # moves the rook
                self.board[move.endRow][move.endCol -
                                        1] = self.board[move.endRow][move.endCol + 1]
                self.board[move.endRow][move.endCol +
                                        1] = '--'  # erase the old rook
            else:  # queen side castle move
                self.board[move.endRow][move.endCol +
                                        1] = self.board[move.endRow][move.endCol - 2]
                self.board[move.endRow][move.endCol -
                                        2] = '--'  # erases the rook

        # update castling rights - whenever it is a rook move or king move
        self.updateCastleRights(move)
        self.castleRightsLog.append(CastleRights(
            self.currentCastlingRight.wks, self.currentCastlingRight.bks,  self.currentCastlingRight.wqs, self.currentCastlingRight.bqs))

        # Update fifty-move counter
        if pawn_moved or piece_captured != '--':
            self.fiftyMoveRule = 0
        else:
            self.fiftyMoveRule += 1

        # Track captured pieces
        if piece_captured != '--':
            self.capturedPieces[piece_captured[0]].append(piece_captured[1])

        # Save position for threefold repetition check
        self.saveCurrentPosition()

    # undo the last move made

    def undoMove(self):
        if len(self.moveLog) != 0:  # make sure there is a move to undo
            move = self.moveLog.pop()
            self.board[move.startRow][move.startCol] = move.pieceMoved
            self.board[move.endRow][move.endCol] = move.pieceCaptured
            self.whiteToMove = not self.whiteToMove  # switch turn back

            # if white king moved
            if move.pieceMoved == 'Wk':
                self.WhiteKingLocation = (move.startRow, move.startCol)
            # if black king moved
            elif move.pieceMoved == 'Bk':
                self.BlackKingLocation = (move.startRow, move.startCol)


            # Undo en passant
            # In the undoMove method, replace the enpassant handling with:
            if move.isEnpassantMove:
                self.board[move.endRow][move.endCol] = '--'
                capturedPawnRow = move.endRow + (1 if move.pieceMoved[0] == 'W' else -1)
                self.board[capturedPawnRow][move.endCol] = (
                    'B' if move.pieceMoved[0] == 'W' else 'W') + 'p'

            # undo the castling rights
            self.castleRightsLog.pop()  # get rid of new castle rights from the move we're undoing
            newRights = self.castleRightsLog[-1]
            self.currentCastlingRight = CastleRights(
                newRights.wks, newRights.bks, newRights.wqs, newRights.bqs)

            # undo castle move
            # In the undoMove method, replace the castle handling with:
            if move.isCastleMove:
                if move.endCol - move.startCol == 2:  # kingside castle
                    self.board[move.endRow][7] = self.board[move.endRow][move.endCol - 1]
                    self.board[move.endRow][move.endCol - 1] = '--'
                else:  # queenside castle
                    self.board[move.endRow][0] = self.board[move.endRow][move.endCol + 1]
                    self.board[move.endRow][move.endCol + 1] = '--'
                    
            # ADD THESE
            self.checkmate = False
            self.stalemate = False
            # Remove the last position
            if len(self.positionLog) > 0:
                self.positionLog.pop()

            # Restore captured piece to the tracker if a piece was uncaptured
            # Restore captured piece to the tracker if a piece was uncaptured
            if move.pieceCaptured != '--':
                self.capturedPieces[move.pieceCaptured[0]].pop()


    # update the castle rights given the move

    def updateCastleRights(self, move):
        if move.pieceMoved == 'Wk':
            self.currentCastlingRight.wks = False
            self.currentCastlingRight.wqs = False
        elif move.pieceMoved == 'Bk':
            self.currentCastlingRight.bks = False
            self.currentCastlingRight.bqs = False
        elif move.pieceMoved == 'Wr':
            if move.startRow == 7:
                if move.startCol == 0:
                    self.currentCastlingRight.wqs = False
                elif move.startCol == 7:
                    self.currentCastlingRight.wks = False
        elif move.pieceMoved == 'Br':
            if move.startRow == 0:
                if move.startCol == 0:
                    self.currentCastlingRight.bqs = False
                elif move.startCol == 7:
                    self.currentCastlingRight.bks = False
    # All the moves considering checks

    def getValidMoves(self):
        tempEnpassantPossible = self.enpassantPossible
        tempCastleRights = CastleRights(
            self.currentCastlingRight.wks, self.currentCastlingRight.bks, self.currentCastlingRight.wqs, self.currentCastlingRight.bqs)

        moves = self.getAllPossibleMoves()
        if self.whiteToMove:
            self.getCastleMoves(
                self.WhiteKingLocation[0], self.WhiteKingLocation[1], moves)
        else:
            self.getCastleMoves(
                self.BlackKingLocation[0], self.BlackKingLocation[1], moves)

        # Create a copy of moves to iterate over while potentially removing items
        movesToRemove = []
        for i in range(len(moves)):
            self.makeMove(moves[i])
            self.whiteToMove = not self.whiteToMove
            if self.inCheck():
                movesToRemove.append(moves[i])
            self.whiteToMove = not self.whiteToMove
            self.undoMove()

        # Remove invalid moves
        for move in movesToRemove:
            if move in moves:
                moves.remove(move)

        if len(moves) == 0:
            if self.inCheck():
                self.checkmate = True
                # Message will be displayed in the UI
            else:
                self.stalemate = True
                # Message will be displayed in the UI
        else:
            self.checkmate = False
            self.stalemate = False

            # Check additional draw conditions
            if self.fiftyMoveRule >= 100:  # 50 moves = 100 half-moves
                self.stalemate = True
                # Set a flag to indicate fifty-move rule draw
                self.drawReason = "fifty-move rule"
            elif self.checkThreefoldRepetition():
                self.stalemate = True
                self.drawReason = "threefold repetition"
            elif self.checkInsufficientMaterial():
                self.stalemate = True
                self.drawReason = "insufficient material"
            else:
                self.drawReason = ""

        self.enpassantPossible = tempEnpassantPossible
        self.currentCastlingRight = tempCastleRights
        return moves
    # checks weather the king is in check

    def inCheck(self):
        if self.whiteToMove:
            return self.isSquareAttacked(self.WhiteKingLocation[0], self.WhiteKingLocation[1])
        else:
            return self.isSquareAttacked(self.BlackKingLocation[0], self.BlackKingLocation[1])

    # checks is the square is being attacked or not
    def isSquareAttacked(self, r, c):
        self.whiteToMove = not self.whiteToMove
        oppomoves = self.getAllPossibleMoves()
        self.whiteToMove = not self.whiteToMove
        for moves in oppomoves:
            if moves.endRow == r and moves.endCol == c:
                return True
        return False

    # ALl the moves without considering checks

    def getAllPossibleMoves(self):
        moves = []
        for r in range(len(self.board)):
            for c in range(len(self.board[r])):
                turn = self.board[r][c][0]
                if (turn == 'W' and self.whiteToMove) or (turn == 'B' and not self.whiteToMove):
                    piece = self.board[r][c][1]
                    self.MoveFunc[piece](r, c, moves)
        return moves

    # get all the pawn moves located at row and col and add these moves to the list

    def getPawnMoves(self, r, c, moves):
        if self.whiteToMove:  # White pawn moves UP the board
            if self.board[r - 1][c] == '--':  # Single square move
                moves.append(Move((r, c), (r - 1, c), self.board))
                # Double move from starting position
                if r == 6 and self.board[r - 2][c] == '--':
                    moves.append(Move((r, c), (r - 2, c), self.board))

            # Capture moves (diagonal left and right)
            if c - 1 >= 0:
                # Normal capture
                if self.board[r - 1][c - 1][0] == 'B':
                    moves.append(Move((r, c), (r - 1, c - 1), self.board))
                # En passant capture (left)
                elif self.enpassantPossible == (r - 1, c - 1):
                    moves.append(Move((r, c), (r - 1, c - 1),
                                      self.board, isEnpassantMove=True))

            if c + 1 <= 7:
                # Normal capture
                if self.board[r - 1][c + 1][0] == 'B':
                    moves.append(Move((r, c), (r - 1, c + 1), self.board))
                # En passant capture (right)
                elif self.enpassantPossible == (r - 1, c + 1):
                    moves.append(Move((r, c), (r - 1, c + 1),
                                      self.board, isEnpassantMove=True))

        else:  # Black pawn moves DOWN the board
            if self.board[r + 1][c] == '--':  # Single square move
                moves.append(Move((r, c), (r + 1, c), self.board))
                # Double move from starting position
                if r == 1 and self.board[r + 2][c] == '--':
                    moves.append(Move((r, c), (r + 2, c), self.board))

            # Capture moves (diagonal left and right)
            if c - 1 >= 0:
                # Normal capture
                if self.board[r + 1][c - 1][0] == 'W':
                    moves.append(Move((r, c), (r + 1, c - 1), self.board))
                # En passant capture (left)
                elif self.enpassantPossible == (r + 1, c - 1):
                    moves.append(Move((r, c), (r + 1, c - 1),
                                      self.board, isEnpassantMove=True))

            if c + 1 <= 7:
                # Normal capture
                if self.board[r + 1][c + 1][0] == 'W':
                    moves.append(Move((r, c), (r + 1, c + 1), self.board))
                # En passant capture (right)
                elif self.enpassantPossible == (r + 1, c + 1):
                    moves.append(Move((r, c), (r + 1, c + 1),
                                      self.board, isEnpassantMove=True))

    # get all the rook moves located at row and col and add these moves to the list

    def getRookMoves(self, r, c, moves):
        # Moves only in a straight file Up, Down, Left, Right
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        enemyColor = 'B' if self.whiteToMove else 'W'

        for d in directions:
            for i in range(1, 8):  # Maximum move length is 7 squares
                endRow = r + d[0] * i
                endCol = c + d[1] * i

                if 0 <= endRow < 8 and 0 <= endCol < 8:  # Ensure within bounds
                    endPiece = self.board[endRow][endCol]
                    if endPiece == "--":  # Empty square, valid move
                        moves.append(
                            Move((r, c), (endRow, endCol), self.board))
                    elif endPiece[0] == enemyColor:  # Enemy piece, valid capture
                        moves.append(
                            Move((r, c), (endRow, endCol), self.board))
                        break  # Stop after capturing
                    else:  # Friendly piece, stop
                        break
                else:  # Out of bounds
                    break

    # get all the  bishop moves located at row and col and add these moves to the list

    def getBishopMoves(self, r, c, moves):
        # moves anywhere diagonally
        directions = [(-1, 1), (1, 1), (1, -1), (-1, -1)]

        enemyColor = 'B' if self.whiteToMove else 'W'

        for d in directions:
            for i in range(1, 8):  # Maximum move length is 7 squares
                endRow = r + d[0] * i
                endCol = c + d[1] * i

                if 0 <= endRow < 8 and 0 <= endCol < 8:  # Ensure within bounds
                    endPiece = self.board[endRow][endCol]
                    if endPiece == "--":  # Empty square, valid move
                        moves.append(
                            Move((r, c), (endRow, endCol), self.board))
                    elif endPiece[0] == enemyColor:  # Enemy piece, valid capture
                        moves.append(
                            Move((r, c), (endRow, endCol), self.board))
                        break  # Stop after capturing
                    else:  # Friendly piece, stop
                        break
                else:  # Out of bounds
                    break
    # get all the knight moves located at row and col and add these moves to the list

    def getKnightMoves(self, r, c, moves):
        # move 2 and a half squares

        # Possible knight moves (L-shaped jumps)
        knightMoves = [
            (2, 1), (2, -1), (-2, 1), (-2, -1),
            (1, 2), (1, -2), (-1, 2), (-1, -2)
        ]

        allyColor = 'W' if self.whiteToMove else 'B'

        for d in knightMoves:
            endRow, endCol = r + d[0], c + d[1]

            if 0 <= endRow < 8 and 0 <= endCol < 8:  # Ensure move is within bounds
                endPiece = self.board[endRow][endCol]
                # Empty or enemy piece
                if endPiece == "--" or endPiece[0] != allyColor:
                    moves.append(Move((r, c), (endRow, endCol), self.board))

    # get all the king moves located at row and col and add these moves to the list

    def getKingMoves(self, r, c, moves):
        # moves anywhere but only one square
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1),
                      (-1, 1), (1, 1), (1, -1), (-1, -1)]

        allyColor = 'W' if self.whiteToMove else 'B'

        for d in directions:
            endRow = r + d[0]
            endCol = c + d[1]

            if 0 <= endRow < 8 and 0 <= endCol < 8:  # Ensure within bounds
                endPiece = self.board[endRow][endCol]
                # Empty or enemy square
                if endPiece == "--" or endPiece[0] != allyColor:
                    moves.append(Move((r, c), (endRow, endCol), self.board))

    # Generate all the valid castle for the king at (r, c) and add them to the list of moves
    def getCastleMoves(self, r, c, moves):
        if self.isSquareAttacked(r, c):
            return  # Can't castle while we're in check

        if (self.whiteToMove and self.currentCastlingRight.wks) or (not self.whiteToMove and self.currentCastlingRight.bks):
            self.getKingsideCastleMoves(r, c, moves)

        if (self.whiteToMove and self.currentCastlingRight.wqs) or (not self.whiteToMove and self.currentCastlingRight.bqs):
            self.getQueensideCastleMoves(r, c, moves)

    def getKingsideCastleMoves(self, r, c, moves):
        if self.board[r][c+1] == '--' and self.board[r][c+2] == '--':
            if not self.isSquareAttacked(r, c+1) and not self.isSquareAttacked(r, c+2):
                moves.append(
                    Move((r, c), (r, c+2), self.board, isCastleMove=True))

    def getQueensideCastleMoves(self, r, c, moves):
        if c-1 >= 0 and c-2 >= 0 and c-3 >= 0:  # Check indices are in bounds
            if self.board[r][c-1] == '--' and self.board[r][c-2] == '--' and self.board[r][c-3] == '--':
                if not self.isSquareAttacked(r, c-1) and not self.isSquareAttacked(r, c-2):
                    moves.append(
                        Move((r, c), (r, c-2), self.board, isCastleMove=True))

    # get all the queen moves located at row and col and add these moves to the list

    def getQueenMoves(self, r, c, moves):
        # goat piece: can move anywhere on the board
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1),
                      (-1, 1), (1, 1), (1, -1), (-1, -1)]

        enemyColor = 'B' if self.whiteToMove else 'W'

        for d in directions:
            for i in range(1, 8):  # Maximum move length is 7 squares
                endRow = r + d[0] * i
                endCol = c + d[1] * i

                if 0 <= endRow < 8 and 0 <= endCol < 8:  # Ensure within bounds
                    endPiece = self.board[endRow][endCol]
                    if endPiece == "--":  # Empty square, valid move
                        moves.append(
                            Move((r, c), (endRow, endCol), self.board))
                    elif endPiece[0] == enemyColor:  # Enemy piece, valid capture
                        moves.append(
                            Move((r, c), (endRow, endCol), self.board))
                        break  # Stop after capturing
                    else:  # Friendly piece, stop
                        break
                else:  # Out of bounds
                    break

    def saveCurrentPosition(self):
        position = []
        for row in self.board:
            position.append(''.join(row))
        position_str = ''.join(position) + ('W' if self.whiteToMove else 'B')
        # Add castling rights to the position string
        position_str += str(int(self.currentCastlingRight.wks)) + str(int(self.currentCastlingRight.wqs)) + \
            str(int(self.currentCastlingRight.bks)) + \
            str(int(self.currentCastlingRight.bqs))
        # Add en passant possibilities
        if self.enpassantPossible:
            position_str += f"{self.enpassantPossible[0]}{self.enpassantPossible[1]}"
        self.positionLog.append(position_str)

    def checkThreefoldRepetition(self):
        """Check if the current position has occurred three times"""
        if len(self.positionLog) >= 5:  # Need at least 5 positions for 3 repetitions
            current_position = self.positionLog[-1]
            repetition_count = self.positionLog.count(current_position)
            return repetition_count >= 3
        return False

    def checkInsufficientMaterial(self):
        """Check if there is insufficient material for checkmate"""
        white_pieces = []
        black_pieces = []

        # Count pieces for each side
        for row in self.board:
            for square in row:
                if square[0] == 'W' and square[1] != 'k':
                    white_pieces.append(square[1])
                elif square[0] == 'B' and square[1] != 'k':
                    black_pieces.append(square[1])

        # King vs King
        if not white_pieces and not black_pieces:
            return True

        # King and Bishop/Knight vs King
        if (len(white_pieces) == 1 and white_pieces[0] in ['b', 'n'] and not black_pieces) or \
                (len(black_pieces) == 1 and black_pieces[0] in ['b', 'n'] and not white_pieces):
            return True

        # King and Bishop vs King and Bishop (same color bishops)
        if len(white_pieces) == 1 and white_pieces[0] == 'b' and \
                len(black_pieces) == 1 and black_pieces[0] == 'b':
            white_bishop_color = None
            black_bishop_color = None

            # Find the bishop squares
            for r in range(8):
                for c in range(8):
                    if self.board[r][c] == 'Wb':
                        white_bishop_color = (r + c) % 2
                    elif self.board[r][c] == 'Bb':
                        black_bishop_color = (r + c) % 2

            # If bishops are on same color squares, it's a draw
            if white_bishop_color == black_bishop_color:
                return True

        return False


class CastleRights():
    def __init__(self, wks, bks, wqs, bqs):
        self.wks = wks
        self.bks = bks
        self.wqs = wqs
        self.bqs = bqs


class Move():
    # maps keys to values
    # key : value
    ranksToRows = {"1": 7, "2": 6, "3": 5,
                   "4": 4, "5": 3, "6": 2, "7": 1, "8": 0}
    rowsToRanks = {v: k for k, v in ranksToRows.items()}
    filesToCols = {"a": 0, "b": 1, "c": 2,
                   "d": 3, "e": 4, "f": 5, "g": 6, "h": 7}
    colsToFiles = {v: k for k, v in filesToCols.items()}

    def __init__(self, startSq, endSq, board, isEnpassantMove=False, isCastleMove=False):
        self.startRow = startSq[0]
        self.startCol = startSq[1]
        self.endRow = endSq[0]
        self.endCol = endSq[1]
        self.pieceMoved = board[self.startRow][self.startCol]
        self.pieceCaptured = board[self.endRow][self.endCol]
        # Pawn Promotion
        self.isPawnPromotion = (self.pieceMoved == 'Wp' and self.endRow == 0) or (
            self.pieceMoved == 'Bp' and self.endRow == 7)
        # En Passant
        self.isEnpassantMove = isEnpassantMove
        # Castle
        self.isCastleMove = isCastleMove

        self.moveId = self.startRow * 1000 + self.startCol * \
            100 + self.endRow * 10 + self.endCol
    # overwritting the equals method

    def __eq__(self, other):
        if isinstance(other, Move):
            return self.moveId == other.moveId
        return False

    def getChessNotation(self):
        # chess notations like 'e2e4', 'e7e5' etc.
        return self.getRankFile(self.startRow, self.startCol) + self.getRankFile(self.endRow, self.endCol)

    def getRankFile(self, r, c):
        return self.colsToFiles[c] + self.rowsToRanks[r]
