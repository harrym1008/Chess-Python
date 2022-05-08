import random

pieceScore = {"K": 0, "Q": 10, "R": 5, "B": 3, "N": 3, "P": 1}

knightScores = [[1, 1, 1, 1, 1, 1, 1, 1],
                [1, 2, 2, 2, 2, 2, 2, 1],
                [1, 2, 3, 3, 3, 3, 2, 1],
                [1, 2, 3, 4, 4, 3, 2, 1],
                [1, 2, 3, 4, 4, 3, 2, 1],
                [1, 2, 3, 3, 3, 3, 2, 1],
                [1, 2, 2, 2, 2, 2, 2, 1],
                [1, 1, 1, 1, 1, 1, 1, 1]]

bishopScores = [[4, 3, 2, 1, 1, 2, 3, 4],
                [3, 4, 3, 2, 2, 3, 4, 3],
                [2, 3, 4, 3, 3, 4, 3, 2],
                [1, 2, 3, 4, 4, 3, 2, 1],
                [1, 2, 3, 4, 4, 3, 2, 1],
                [2, 3, 4, 3, 3, 4, 3, 2],
                [3, 4, 3, 2, 2, 3, 4, 3],
                [4, 3, 2, 1, 1, 2, 3, 4]]

queenScores = [[1, 1, 1, 3, 1, 1, 1, 1],
               [1, 2, 3, 3, 3, 1, 1, 1],
               [1, 4, 3, 3, 3, 4, 2, 1],
               [1, 2, 3, 3, 3, 2, 2, 1],
               [1, 2, 3, 3, 3, 2, 2, 1],
               [1, 4, 3, 3, 3, 4, 2, 1],
               [1, 2, 3, 3, 3, 1, 1, 1],
               [1, 1, 1, 3, 1, 1, 1, 1]]

rookScores = [[4, 3, 4, 4, 4, 4, 3, 4],
              [4, 4, 4, 4, 4, 4, 4, 4],
              [1, 1, 2, 3, 3, 2, 1, 1],
              [1, 2, 3, 4, 4, 3, 2, 1],
              [1, 2, 3, 4, 4, 3, 2, 1],
              [1, 1, 2, 3, 3, 2, 1, 1],
              [4, 4, 4, 4, 4, 4, 4, 4],
              [4, 3, 4, 4, 4, 4, 3, 4]]

whitePawnScores = [[9, 9, 10, 12, 12, 10, 9, 9],
                   [7, 7, 8, 8, 8, 8, 7, 7],
                   [5, 6, 6, 7, 7, 6, 6, 5],
                   [2, 3, 3, 5, 5, 3, 3, 2],
                   [1, 2, 3, 4, 4, 3, 2, 1],
                   [1, 1, 2, 3, 3, 2, 1, 1],
                   [1, 1, 1, 0, 0, 1, 1, 1],
                   [0, 0, 0, 0, 0, 0, 0, 0]]

kingScores = [[-4, 0, 0, 0, 0, 0, 0, -4],
              [0 for i in range(8)],
              [0 for i in range(8)],
              [0 for i in range(8)],
              [0 for i in range(8)],
              [0 for i in range(8)],
              [0 for i in range(8)],
              [-4, 0, 0, 0, 0, 0, 0, -4]]

blackPawnScores = whitePawnScores[0:]
blackPawnScores.reverse()

piecePositionScores = {"N": knightScores, "B": bishopScores, "Q": queenScores, "K": kingScores,
                       "R": rookScores, "wP": whitePawnScores, "bP": blackPawnScores}

CHECKMATE = 1000
STALEMATE = 0
DEPTH_MINMAX = 2
DEPTH_NEGAMAX = 2


def GetMove(skillLevel, validMoves, gs, returnQueue):
    global counter
    counter = 0
    m = None
    if skillLevel == 1:  # 1: Random
        m = RandomMove(validMoves), counter
    elif skillLevel == 2:  # 2: Aggressive
        m = AggressiveRandom(validMoves), counter
    elif skillLevel == 3:  # 3: Greedy Algorithm
        m = GreedyAlgorithm(gs, validMoves), counter
    elif skillLevel == 4:  # 4: MinMax Algorithm
        m = FindBestMoveMinMax(gs, validMoves), counter
    elif skillLevel == 5:  # 6: NegaMax Algorithm with Alpha Beta Pruning
        m = FindBestMoveNegaMaxAlphaBeta(gs, validMoves), counter
    returnQueue.put(m)


def GreedyAlgorithm(gs, validMoves):
    global counter
    turnMultiplier = 1 if gs.whiteToMove else -1
    opponentMinMaxScore = CHECKMATE
    bestPlayerMove = None
    random.shuffle(validMoves)
    for playerMove in validMoves:
        gs.MakeMove(playerMove)
        opponentsMoves = gs.GetValidMoves()
        if gs.stalemate:
            opponentMaxScore = STALEMATE
        elif gs.checkmate:
            opponentMaxScore = -CHECKMATE
        else:
            opponentMaxScore = -CHECKMATE
            for opponentMove in opponentsMoves:
                gs.MakeMove(opponentMove)
                gs.GetValidMoves()
                if gs.checkmate:
                    score = CHECKMATE
                elif gs.stalemate:
                    score = STALEMATE
                else:
                    score = -turnMultiplier * ScoreMaterial(gs.board)
                if score > opponentMaxScore:
                    opponentMaxScore = score
                gs.UndoMove()
        if opponentMaxScore < opponentMinMaxScore:
            opponentMinMaxScore = opponentMaxScore
            bestPlayerMove = playerMove
        gs.UndoMove()
    return bestPlayerMove


# Helper method to make the first recursive call
def FindBestMoveMinMax(gs, validMoves):
    global nextMove
    nextMove = None
    random.shuffle(validMoves)
    FindMoveMinMax(gs, validMoves, DEPTH_MINMAX, gs.whiteToMove)
    return nextMove


def FindMoveMinMax(gs, validMoves, depth, whiteToMove):
    global nextMove, counter
    if depth == 0:
        return ScoreMaterial(gs.board)

    if whiteToMove:
        maxScore = -CHECKMATE
        for move in validMoves:
            gs.MakeMove(move)
            nextMoves = gs.GetValidMoves()
            score = FindMoveMinMax(gs, nextMoves, depth - 1, False)
            if score > maxScore:
                maxScore = score
                if depth == DEPTH_MINMAX:
                    nextMove = move
            gs.UndoMove()
        return maxScore

    else:
        minScore = CHECKMATE
        for move in validMoves:
            gs.MakeMove(move)
            nextMoves = gs.GetValidMoves()
            score = FindMoveMinMax(gs, nextMoves, depth - 1, True)
            if score < minScore:
                minScore = score
                if depth == DEPTH_MINMAX:
                    nextMove = move
            gs.UndoMove()
        return minScore


def FindBestMoveNegaMax(gs, validMoves):
    global nextMove
    nextMove = None
    random.shuffle(validMoves)
    FindMoveNegaMax(gs, validMoves, DEPTH_NEGAMAX, 1 if gs.whiteToMove else -1)
    return nextMove


def FindMoveNegaMax(gs, validMoves, depth, turnMultiplier):
    global nextMove
    if depth == 0:
        return turnMultiplier * ScoreBoard(gs)

    maxScore = -CHECKMATE
    for move in validMoves:
        gs.MakeMove(move)
        nextMoves = gs.GetValidMoves()
        score = -FindMoveNegaMax(gs, nextMoves, depth - 1, -turnMultiplier)
        if score > maxScore:
            maxScore = score
            if depth == DEPTH_NEGAMAX:
                nextMove = move
        gs.UndoMove()
    return maxScore


def FindBestMoveNegaMaxAlphaBeta(gs, validMoves):
    global nextMove
    nextMove = None
    random.shuffle(validMoves)
    FindMoveNegaMaxAlphaBeta(gs, validMoves, DEPTH_NEGAMAX, -CHECKMATE, CHECKMATE, 1 if gs.whiteToMove else -1)
    return nextMove


def FindMoveNegaMaxAlphaBeta(gs, validMoves, depth, alpha, beta, turnMultiplier):
    global nextMove
    if depth == 0:
        return turnMultiplier * ScoreBoard(gs)

    # move ordering - implement later
    maxScore = -CHECKMATE
    for move in validMoves:
        gs.MakeMove(move)
        nextMoves = gs.GetValidMoves()
        score = -FindMoveNegaMaxAlphaBeta(gs, nextMoves, depth - 1, -beta, -alpha, -turnMultiplier)
        if score > maxScore:
            maxScore = score
            if depth == DEPTH_NEGAMAX:
                nextMove = move
                print(f"{move}: {round(score * 10) / 10}")
        gs.UndoMove()
        if maxScore > alpha:  # pruning
            alpha = maxScore
        if alpha >= beta:
            break
    return maxScore


# Positive score is good for white
# Negative score is good for black

def ScoreBoard(gs):
    global counter
    counter += 1

    if gs.checkmate:
        if gs.whiteToMove:
            return -CHECKMATE  # black wins
        else:
            return CHECKMATE  # white wins
    elif gs.stalemate:
        return STALEMATE

    score = 0
    for row in range(len(gs.board)):
        for col in range(len(gs.board[row])):
            square = gs.board[row][col]
            if square != "--":
                # score positionally

                if square[1] == "P":  # for pawns
                    piecePositionScore = piecePositionScores[square][row][col]
                else:  # for other pieces
                    piecePositionScore = piecePositionScores[square[1]][row][col]

                if square[0] == "w":
                    score += pieceScore[square[1]] + piecePositionScore * 0.1
                elif square[0] == "b":
                    score -= pieceScore[square[1]] + piecePositionScore * 0.1
    return score


# get score based on the board's pieces
def ScoreMaterial(board):
    score = 0
    for row in board:
        for square in row:
            if square[0] == "w":
                score += pieceScore[square[1]]
            elif square[0] == "b":
                score -= pieceScore[square[1]]
    return score


def RandomMove(validMoves):  # skill level 1
    return validMoves[random.randint(0, len(validMoves) - 1)]


def AggressiveRandom(validMoves):  # skill level 2
    goodMoves = []
    for move in validMoves:
        if move.pieceCaptured != "--":
            goodMoves.append(move)
    if len(goodMoves) > 0:
        return goodMoves[random.randint(0, len(goodMoves) - 1)]
    else:
        return RandomMove(validMoves)
