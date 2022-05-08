"""
This class is responsible for storing all the information about the current state of the chess game
Also responsible for determining the valid moves at current state
Also keeps a move log
"""


class GameState:
    def __init__(self):
        # board is 8x8 2d list, each element has 2 chars
        # first char is piece colour, second char is the piece type
        # "--" is an empty space with no piece
        self.board = [
            ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
            ["bP", "bP", "bP", "bP", "bP", "bP", "bP", "bP"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["wP", "wP", "wP", "wP", "wP", "wP", "wP", "wP"],
            ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"]]
        self.moveFunctions = {"P": self.GetPawnMoves, "R": self.GetRookMoves,
                              "N": self.GetKnightMoves, "B": self.GetBishopMoves,
                              "Q": self.GetQueenMoves, "K": self.GetKingMoves}

        self.whiteToMove = True
        self.moveLog = []
        self.whiteKingLocation = (7, 4)
        self.blackKingLocation = (0, 4)
        self.checkmate = False
        self.stalemate = False
        self.enPassantPossible = ()  # coordinates for a square where an en passant capture is possible
        self.enPassantPossibleLog = [self.enPassantPossible]
        self.currentCastlingRights = CastleRights(True, True, True, True)
        self.castleRightsLog = [CastleRights(self.currentCastlingRights.wks, self.currentCastlingRights.bks,
                                             self.currentCastlingRights.wqs, self.currentCastlingRights.bqs)]

    # Fen string manager
    def FenString(self, fen=None):
        if fen is not None:  # converting to fen string
            self.board = []
            for row in fen.split("/"):
                brow = []
                for c in row:
                    if c == " ":
                        break
                    elif c in "12345678":
                        brow.extend(["--"] * int(c))
                    elif c > "Z":
                        brow.append("b" + c.upper())
                    else:
                        brow.append("w" + c)
                self.board.append(brow)

        else:  # updating from fen string
            fen = ""
            for row in self.board:
                empty = 0
                for cell in row:
                    c = cell[0]
                    if c in ("w", "b"):
                        if empty > 0:
                            fen = f"{fen}{empty}"
                            empty = 0
                        fen = f"{fen}{cell[1].upper() if c == 'w' else cell[1].lower()}"
                    else:
                        empty += 1
                if empty > 0:
                    fen = f"{fen}{empty}"
                fen = f"{fen}/"
            return fen[:-1]

    # takes a Move as a parameter and executes it

    def MakeMove(self, move):
        self.board[move.startRow][move.startCol] = "--"  # no piece at old pos
        self.board[move.endRow][move.endCol] = move.pieceMoved  # new piece at new pos
        self.moveLog.append(move)  # add move to move log
        self.whiteToMove = not self.whiteToMove  # swap players

        # update kings location
        if move.pieceMoved == "wK":
            self.whiteKingLocation = (move.endRow, move.endCol)
        elif move.pieceMoved == "bK":
            self.blackKingLocation = (move.endRow, move.endCol)

        # pawn promotion
        if move.isPawnPromotion:
            self.board[move.endRow][move.endCol] = move.pieceMoved[0] + "Q"

        # en passant
        if move.isEnpassantMove:
            self.board[move.startRow][move.endCol] = "--"  # capturing the pawn

        # update enpassantPossible variable
        if move.pieceMoved[1] == "P" and abs(move.startRow - move.endRow) == 2:  # only on 2 square pawn advances
            self.enPassantPossible = ((move.startRow + move.endRow) // 2, move.endCol)
        else:
            self.enPassantPossible = ()

        self.enPassantPossibleLog.append(self.enPassantPossible)

        # castling
        if move.isCastleMove:
            if move.endCol - move.startCol == 2:  # moved kingside
                self.board[move.endRow][move.endCol - 1] = self.board[move.endRow][move.endCol + 1]  # move rook
                self.board[move.endRow][move.endCol + 1] = "--"  # erase old pos rook
            else:  # moved queenside
                self.board[move.endRow][move.endCol + 1] = self.board[move.endRow][move.endCol - 2]  # move rook
                self.board[move.endRow][move.endCol - 2] = "--"

        # update castling rights - whenever it is a rook or a king move
        self.UpdateCastleRights(move)
        self.castleRightsLog.append(CastleRights(self.currentCastlingRights.wks, self.currentCastlingRights.bks,
                                                 self.currentCastlingRights.wqs, self.currentCastlingRights.bqs))

    # undo the last move
    def UndoMove(self):
        if len(self.moveLog) != 0:  # make sure you can undo
            move = self.moveLog.pop(-1)
            self.board[move.startRow][move.startCol] = move.pieceMoved  # no piece at old pos
            self.board[move.endRow][move.endCol] = move.pieceCaptured  # new piece at new pos
            self.whiteToMove = not self.whiteToMove  # swap players

            # update kings location
            if move.pieceMoved == "wK":
                self.whiteKingLocation = (move.startRow, move.startCol)
            elif move.pieceMoved == "bK":
                self.blackKingLocation = (move.startRow, move.startCol)
            if move.isEnpassantMove:
                self.board[move.endRow][move.endCol] = "--"  # leave landing square blank
                self.board[move.startRow][move.endCol] = move.pieceCaptured

            self.enPassantPossibleLog.pop()
            self.enPassantPossible = self.enPassantPossibleLog[-1]

            # undo castling rights
            self.castleRightsLog.pop()  # get rid of new castle rights from the move we are undoing
            self.currentCastlingRights = CastleRights(self.castleRightsLog[-1].wks, self.castleRightsLog[-1].bks,
                                                      self.castleRightsLog[-1].wqs, self.castleRightsLog[-1].bqs)
            # undo castle move
            if move.isCastleMove:
                if move.endCol - move.startCol == 2:  # kingside
                    self.board[move.endRow][move.endCol + 1] = self.board[move.endRow][move.endCol - 1]
                    self.board[move.endRow][move.endCol - 1] = "--"
                else:  # queenside
                    self.board[move.endRow][move.endCol - 2] = self.board[move.endRow][move.endCol + 1]
                    self.board[move.endRow][move.endCol + 1] = "--"

            self.checkmate = False
            self.stalemate = False

    # update the castle rights given the move
    def UpdateCastleRights(self, move):
        if move.pieceMoved == "wK":
            self.currentCastlingRights.wks = False
            self.currentCastlingRights.wqs = False
        elif move.pieceMoved == "bK":
            self.currentCastlingRights.bks = False
            self.currentCastlingRights.bqs = False
        elif move.pieceMoved == "wR":
            if move.startRow == 7:
                if move.startCol == 0:  # left white rook
                    self.currentCastlingRights.wqs = False
                elif move.startCol == 7:  # right white rook
                    self.currentCastlingRights.wks = False
        elif move.pieceMoved == "bR":
            if move.startRow == 0:
                if move.startCol == 0:  # left black rook
                    self.currentCastlingRights.bqs = False
                elif move.startCol == 7:  # right black rook
                    self.currentCastlingRights.bks = False

        # if a rook is captured
        if move.pieceCaptured == "wR":
            if move.endRow == 7:
                if move.endCol == 0:
                    self.currentCastlingRights.wqs = False
                elif move.endCol == 7:
                    self.currentCastlingRights.wks = False
        elif move.pieceCaptured == "bR":
            if move.endRow == 0:
                if move.endCol == 0:
                    self.currentCastlingRights.bqs = False
                elif move.endCol == 7:
                    self.currentCastlingRights.bks = False

    # All moves considering checks
    def GetValidMoves(self):
        tempEnpassantPossible = self.enPassantPossible
        tempCastleRights = CastleRights(self.currentCastlingRights.wks, self.currentCastlingRights.bks,
                                        self.currentCastlingRights.wqs, self.currentCastlingRights.bqs)
        # 1) Generate possible moves
        moves = self.GetAllPossibleMoves()
        if self.whiteToMove:
            self.GetCastleMoves(self.whiteKingLocation[0], self.whiteKingLocation[1], moves)
        else:
            self.GetCastleMoves(self.blackKingLocation[0], self.blackKingLocation[1], moves)

        # 2) For each move, make the move
        for i in range(len(moves) - 1, -1, -1):  # when removing from a list, go backwards
            self.MakeMove(moves[i])
            self.whiteToMove = not self.whiteToMove
            # 3) Generate all opponent's moves
            # 4) For each of your opponent  's moves, see if they attack your king
            if self.InCheck():
                # 5) If they do attack your king, not a valid move
                moves.remove(moves[i])
            self.whiteToMove = not self.whiteToMove
            self.UndoMove()

        if len(moves) == 0:  # Check checkmate or stalemate
            if self.InCheck():
                self.checkmate = True
            else:
                self.stalemate = True
        else:
            self.checkmate = False
            self.stalemate = False

        self.enPassantPossible = tempEnpassantPossible
        self.currentCastlingRights = tempCastleRights
        return moves

    # Determines if the current player is in check
    def InCheck(self):
        if self.whiteToMove:
            return self.SquareUnderAttack(self.whiteKingLocation[0], self.whiteKingLocation[1])
        else:
            return self.SquareUnderAttack(self.blackKingLocation[0], self.blackKingLocation[1])

    # Determines if the enemy can attack the square (r, c)
    def SquareUnderAttack(self, r, c):
        self.whiteToMove = not self.whiteToMove  # switch to opponents turn
        oppMoves = self.GetAllPossibleMoves()  # get all opponents moves
        self.whiteToMove = not self.whiteToMove  # switch turn back
        for move in oppMoves:
            if move.endRow == r and move.endCol == c:  # square is under attack!
                return True
        return False

    def AmIInCheck(self):
        if self.whiteToMove:
            return self.SquareUnderAttack(self.whiteKingLocation[0], self.whiteKingLocation[1])
        else:
            return self.SquareUnderAttack(self.blackKingLocation[0], self.blackKingLocation[1])

    # All moves without considering checks
    def GetAllPossibleMoves(self):
        moves = []
        for r in range(len(self.board)):  # num of rows
            for c in range(len(self.board[r])):  # num of columns in given row
                turn = self.board[r][c][0]
                if (turn == "w" and self.whiteToMove) or (turn == "b" and not self.whiteToMove):
                    piece = self.board[r][c][1]
                    self.moveFunctions[piece](r, c, moves)  # calls the appropriate move function
        return moves

    # get all pawn moves at row, col, and these to the moves list
    def GetPawnMoves(self, r, c, moves):
        if self.whiteToMove:  # white pawn moves
            if self.board[r - 1][c] == "--":  # 1 square pawn advance
                moves.append(Move((r, c), (r - 1, c), self.board))
                try:
                    if self.board[r - 2][c] == "--" and r == 6:  # 2 square pawn advance
                        moves.append(Move((r, c), (r - 2, c), self.board))
                except:
                    pass
            if c - 1 >= 0:
                if self.board[r - 1][c - 1][0] == "b":  # enemy capture to the left
                    moves.append(Move((r, c), (r - 1, c - 1), self.board))
                elif (r - 1, c - 1) == self.enPassantPossible:
                    moves.append(Move((r, c), (r - 1, c - 1), self.board, isEnpassantMove=True))
            if c + 1 <= 7:
                if self.board[r - 1][c + 1][0] == "b":  # enemy capture to the right
                    moves.append(Move((r, c), (r - 1, c + 1), self.board))
                elif (r - 1, c + 1) == self.enPassantPossible:
                    moves.append(Move((r, c), (r - 1, c + 1), self.board, isEnpassantMove=True))

        else:  # black pawn moves
            if self.board[r + 1][c] == "--":  # 1 square pawn advance
                moves.append(Move((r, c), (r + 1, c), self.board))
                try:
                    if self.board[r + 2][c] == "--" and r == 1:  # 2 square pawn advance
                        moves.append(Move((r, c), (r + 2, c), self.board))
                except:
                    pass
            if c - 1 >= 0:
                if self.board[r + 1][c - 1][0] == "w":  # enemy capture to the left
                    moves.append(Move((r, c), (r + 1, c - 1), self.board))
                elif (r + 1, c - 1) == self.enPassantPossible:
                    moves.append(Move((r, c), (r + 1, c - 1), self.board, isEnpassantMove=True))
            if c + 1 <= 7:
                if self.board[r + 1][c + 1][0] == "w":  # enemy capture to the right
                    moves.append(Move((r, c), (r + 1, c + 1), self.board))
                elif (r + 1, c + 1) == self.enPassantPossible:
                    moves.append(Move((r, c), (r + 1, c + 1), self.board, isEnpassantMove=True))

    # get all rook moves at row, col, and add these to the move list
    def GetRookMoves(self, r, c, moves):
        directions = ((-1, 0), (0, -1), (1, 0), (0, 1))  # up, left, down, right
        enemyColour = "b" if self.whiteToMove else "w"
        for d in directions:
            for i in range(1, 8):
                endRow = r + d[0] * i  # keep moving in direction
                endCol = c + d[1] * i
                if 0 <= endRow < 8 and 0 <= endCol < 8:  # check if it is on board
                    endPiece = self.board[endRow][endCol]
                    if endPiece == "--":  # valid empty space
                        moves.append(Move((r, c), (endRow, endCol), self.board))
                    elif endPiece[0] == enemyColour:  # can capture enemy
                        moves.append(Move((r, c), (endRow, endCol), self.board))
                        break
                    else:  # hit an allied piece
                        break
                else:  # off board
                    break

    # get all knight moves at row, col, and add these to the move list
    def GetKnightMoves(self, r, c, moves):
        knightMoves = ((-2, -1), (-2, 1), (-1, -2), (1, -2), (1, 2), (2, -1), (2, 1), (-1, 2))  # all knight moves
        allyColour = "w" if self.whiteToMove else "b"
        for m in knightMoves:
            endRow = r + m[0]
            endCol = c + m[1]
            if 0 <= endRow < 8 and 0 <= endCol < 8:
                endPiece = self.board[endRow][endCol]
                if endPiece[0] != allyColour:  # valid empty space
                    moves.append(Move((r, c), (endRow, endCol), self.board))

    # get all bishop moves at row, col, and add these to the move list
    def GetBishopMoves(self, r, c, moves):
        directions = ((-1, -1), (-1, 1), (1, -1), (1, 1))  # all diagonal directions
        enemyColour = "b" if self.whiteToMove else "w"
        for d in directions:
            for i in range(1, 8):
                endRow = r + d[0] * i  # keep moving in direction
                endCol = c + d[1] * i
                if 0 <= endRow < 8 and 0 <= endCol < 8:  # check if it is on board
                    endPiece = self.board[endRow][endCol]
                    if endPiece == "--":  # valid empty space
                        moves.append(Move((r, c), (endRow, endCol), self.board))
                    elif endPiece[0] == enemyColour:  # can capture enemy
                        moves.append(Move((r, c), (endRow, endCol), self.board))
                        break
                    else:  # hit an allied piece
                        break
                else:  # off board
                    break

    # get all queen moves at row, col, and add these to the move list
    def GetQueenMoves(self, r, c, moves):
        self.GetRookMoves(r, c, moves)
        self.GetBishopMoves(r, c, moves)

    # get all king moves at row, col, and add these to the move list
    def GetKingMoves(self, r, c, moves):
        kingMoves = ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1))
        allyColour = "w" if self.whiteToMove else "b"
        for i in range(8):
            endRow = r + kingMoves[i][0]
            endCol = c + kingMoves[i][1]
            if 0 <= endRow < 8 and 0 <= endCol < 8:
                endPiece = self.board[endRow][endCol]
                if endPiece[0] != allyColour:
                    moves.append(Move((r, c), (endRow, endCol), self.board))

    # generate all valid castle moves for the king at (r, c) and add them to the list of moves
    def GetCastleMoves(self, r, c, moves):
        if self.SquareUnderAttack(r, c):
            return  # can't castle while in check
        if (self.whiteToMove and self.currentCastlingRights.wks) or (
                not self.whiteToMove and self.currentCastlingRights.bks):
            self.GetKingsideCastleMoves(r, c, moves)
        if (self.whiteToMove and self.currentCastlingRights.wqs) or (
                not self.whiteToMove and self.currentCastlingRights.bqs):
            self.GetQueensideCastleMoves(r, c, moves)

    def GetKingsideCastleMoves(self, r, c, moves):
        if self.board[r][c + 1] == "--" and self.board[r][c + 2] == "--" and \
                not self.SquareUnderAttack(r, c + 1) and not self.SquareUnderAttack(r, c + 2):
            moves.append(Move((r, c), (r, c + 2), self.board, isCastleMove=True))

    def GetQueensideCastleMoves(self, r, c, moves):
        if self.board[r][c - 1] == "--" and self.board[r][c - 2] == "--" and self.board[r][c - 3] == "--" and \
                not self.SquareUnderAttack(r, c - 1) and not self.SquareUnderAttack(r, c - 2):
            moves.append(Move((r, c), (r, c - 2), self.board, isCastleMove=True))


class CastleRights:
    def __init__(self, wks, bks, wqs, bqs):
        self.wks, self.bks, self.wqs, self.bqs = wks, bks, wqs, bqs  # store current state of castling rights

    def __str__(self):
        return f"{self.wks}, {self.wqs}, {self.bks}, {self.bqs}"


class Move:
    # maps keys to values
    ranksToRows = {}
    for i in range(1, 9):
        ranksToRows[str(i)] = 8 - i
    filesToCols = {"a": 0, "b": 1, "c": 2, "d": 3, "e": 4, "f": 5, "g": 6, "h": 7}
    rowsToRanks = {v: k for k, v in ranksToRows.items()}
    colsToFiles = {v: k for k, v in filesToCols.items()}

    def __init__(self, startSq, endSq, board, isEnpassantMove=False, isCastleMove=False):
        self.startRow = startSq[0]
        self.startCol = startSq[1]
        self.endRow = endSq[0]
        self.endCol = endSq[1]

        self.pieceMoved = board[self.startRow][self.startCol]
        self.pieceCaptured = board[self.endRow][self.endCol]
        self.moveID = self.startRow * 1000 + self.startCol * 100 + self.endRow * 10 + self.endCol

        # pawn promotion
        self.isPawnPromotion = (self.pieceMoved == "wP" and self.endRow == 0) or \
                               (self.pieceMoved == "bP" and self.endRow == 7)

        # en passant
        self.isEnpassantMove = isEnpassantMove
        if self.isEnpassantMove:
            self.pieceCaptured = "wP" if self.pieceMoved == "bP" else "bP"

        # castling
        self.isCastleMove = isCastleMove
        self.isCapture = self.pieceCaptured != "--"

        self.isCheckMove = False
        self.isCheckmateMove = False
        self.isStalemateMove = False

    # override the equals method
    def __eq__(self, other):
        if isinstance(other, Move):
            return self.moveID == other.moveID
        return False

    def GetChessNotation(self) -> str:
        return str(self)

    def GetRankFile(self, r, c):
        return self.colsToFiles[c] + self.rowsToRanks[r]

    def __str__(self, gameState=None):
        # castle move
        if self.isCastleMove:
            return "O-O" if self.endCol == 6 else "O-O-O"  # king side castle or queen side castle

        endSquare = self.GetRankFile(self.endRow, self.endCol)
        # pawn moves
        if self.pieceMoved[1] == "P":
            pawnPromotionEnd = "Q" if self.isPawnPromotion else ""
            if self.isCapture:
                return f"{self.colsToFiles[self.startCol]}x{endSquare}{pawnPromotionEnd}"
            else:
                return f"{endSquare}{pawnPromotionEnd}"

        moveString = self.pieceMoved[1]
        if self.isCapture:
            moveString += "x"

        moveString += endSquare

        if self.isCheckmateMove:
            moveString += "#"
        elif self.isStalemateMove:
            moveString += "="
        elif self.isCheckMove:
            moveString += "+"

        return moveString

    def UpdateFromGameState(self, gameState):
        if gameState is not None:
            if gameState.checkmate:
                self.isCheckmateMove = True
            elif gameState.stalemate:
                self.isStalemateMove = True
            elif gameState.AmIInCheck():
                self.isCheckMove = True
