"""
Driver file
Handles user input and displays current game state
"""

from multiprocessing import Process, Queue

import os
import pygame as p
import pygame.time

import BorderedText
import ChessEngine
import SmartMoveFinder

os.system("cls")
BOARD_WIDTH = BOARD_HEIGHT = 512

if __name__ == "__main__":
    BOARD_WIDTH = BOARD_HEIGHT = int(input("\nInput vertical resolution: "))

TXT_MULTIPLIER = BOARD_HEIGHT / 512
MOVE_LOG_PANEL_WIDTH = 256 * TXT_MULTIPLIER
MOVE_LOG_PANEL_HEIGHT = BOARD_HEIGHT
DIMENSION = 8  # 8x8 board
SQ_SIZE = BOARD_HEIGHT // DIMENSION
MAX_FPS = 60
IMAGES = {}
FONTS = []

MUSIC = 1

RANKS = "87654321"
FILES = "abcdefgh"


# Creating global dict of images
def LoadImages():
    SIZE_MULTIPLIER = 1
    pieces = ["wP", "wR", "wN", "wB", "wK", "wQ", "bP", "bR", "bN", "bB", "bK", "bQ", "--", "CaptureSquare"]
    try:
        for piece in pieces:
            IMAGES[piece] = p.transform.scale(p.image.load("Chess/images/" + piece + ".png"),
                                              (SQ_SIZE * SIZE_MULTIPLIER, SQ_SIZE * SIZE_MULTIPLIER))
    except:
        for piece in pieces:
            IMAGES[piece] = p.transform.scale(p.image.load("images/" + piece + ".png"),
                                              (SQ_SIZE * SIZE_MULTIPLIER, SQ_SIZE * SIZE_MULTIPLIER))



def LoadFonts():
    global FONTS
    FONTS = [p.font.SysFont("Arial", round(64 * TXT_MULTIPLIER), True, False),
             p.font.SysFont("Arial", round(24 * TXT_MULTIPLIER), True, False),
             p.font.SysFont("Arial", round(20 * TXT_MULTIPLIER), False, False),
             p.font.SysFont("Arial", round(20 * TXT_MULTIPLIER), False, True),
             p.font.SysFont("Arial", round(32 * TXT_MULTIPLIER), True, False),
             p.font.SysFont("Arial", round(16 * TXT_MULTIPLIER), True, False)]


# Main driver for code. Handles user input and updates graphics
def Main():
    global animating, screen, clock, gs

    gameType = GetGameType()

    p.init()
    screen = p.display.set_mode((BOARD_WIDTH + MOVE_LOG_PANEL_WIDTH, BOARD_HEIGHT))
    clock = pygame.time.Clock()
    screen.fill(p.Color("white"))
    gs = ChessEngine.GameState()
    validMoves = gs.GetValidMoves()
    moveMade = False  # flag variable for when a move is made
    animating = False
    gameOver = False
    player1 = gameType[0]  # If a human is playing white, this will be 0. If an AI is playing, it will be AI skill level
    player2 = gameType[1]  # Same as above but for black

    AIThinking = False
    moveFinderProcess = None
    moveUndone = False

    LoadImages()  # only run once
    LoadFonts()

    running = True
    sqSelected = ()  # no square select, keeps track of last click of the user
    playerClicks = []  # keep track of player clicks

    DrawGameState(screen, gs, validMoves, sqSelected)
    ChangeMusic(0)

    while running:
        humanTurn = (gs.whiteToMove and player1 == 0) or (not gs.whiteToMove and player2 == 0)

        for e in p.event.get():
            if e.type == p.QUIT:
                running = False
            # mouse handler
            elif e.type == p.MOUSEBUTTONDOWN:
                if not gameOver and humanTurn:
                    location = p.mouse.get_pos()  # (x, y) location of mouse
                    mouseCol, mouseRow = location[0] // SQ_SIZE, location[1] // SQ_SIZE
                    if sqSelected == (mouseRow, mouseCol) or mouseCol >= 8:  # clicked the same square twice
                        sqSelected = ()  # or clicked the move log
                        playerClicks = []
                    elif sqSelected == () and gs.board[mouseRow][mouseCol] == "--":
                        pass
                    else:
                        sqSelected = mouseRow, mouseCol  # append for both 1st and 2nd clicks
                        playerClicks.append(sqSelected)

                    if len(playerClicks) == 2:
                        move = ChessEngine.Move(playerClicks[0], playerClicks[1], gs.board)
                        for i in range(len(validMoves)):
                            if move == validMoves[i]:
                                gs.MakeMove(validMoves[i])
                                moveMade = True
                                animating = True
                                sqSelected = ()
                                playerClicks = []
                        if not moveMade:
                            playerClicks = [sqSelected]
            # key handler
            elif e.type == p.KEYDOWN:
                if e.key == p.K_z:  # undo when 'z' is pressed
                    gs.UndoMove()
                    validMoves = gs.GetValidMoves()
                    moveMade = True
                    animating = False
                    gameOver = False
                    if AIThinking:
                        moveFinderProcess.terminate()
                        AIThinking = False
                    moveUndone = True
                if e.key == p.K_r:  # reset when 'r' is pressed
                    gs = ChessEngine.GameState()
                    validMoves = gs.GetValidMoves()
                    sqSelected = ()
                    playerClicks = []
                    moveMade = False
                    animating = False
                    gameOver = False
                    if AIThinking:
                        moveFinderProcess.terminate()
                        AIThinking = False
                    moveUndone = True

        # AI move finder
        if not gameOver and not humanTurn and not moveUndone:
            if not AIThinking:
                AIThinking = True
                print("AI is thinking...")
                skillLevel = player1 if gs.whiteToMove else player2

                returnQueue = Queue()   # used to pass data between threads
                moveFinderProcess = Process(target=SmartMoveFinder.GetMove,
                                            args=(skillLevel, validMoves, gs, returnQueue))
                moveFinderProcess.start()   # call SmartMoveFinder.GetMove(skillLevel, validMoves, gs)

            if not moveFinderProcess.is_alive():
                AIMove = returnQueue.get()
                if AIMove[0] is None:
                    AIMove = SmartMoveFinder.RandomMove(validMoves), 1
                gs.MakeMove(AIMove[0])
                print(f"{'White' if not gs.whiteToMove else 'Black'} AI is done thinking."
                      f" Chose '{str(AIMove[0])}. Boards: {AIMove[1]}")
                moveMade = True
                animating = True
                AIThinking = False


        if moveMade:
            if animating:
                AnimateMove(gs.moveLog[-1], screen, gs.board, clock)
            validMoves = gs.GetValidMoves()
            gs.moveLog[-1].UpdateFromGameState(gs)
            if gs.AmIInCheck() and not gs.checkmate:
                DrawCheckText(screen, gs, clock)
                ChangeMusic(1)
            else:
                ChangeMusic(0)
            moveMade = False
            animating = False
            moveUndone = False

        DrawGameState(screen, gs, validMoves, sqSelected)

        if isinstance(moveFinderProcess, Process):
            if moveFinderProcess.is_alive():
                DrawAIThinking(screen, gs.whiteToMove)


        if gs.checkmate:
            gameOver = True
            if gs.whiteToMove:
                DrawEndGameText(screen, "Checkmate!", 64, (0, 20))
                DrawEndGameText(screen, "Black wins", 32, (0, -40))
            else:
                DrawEndGameText(screen, "Checkmate!", 64, (0, 20))
                DrawEndGameText(screen, "White wins", 32, (0, -40))
        elif gs.stalemate:
            gameOver = True
            DrawEndGameText(screen, "Stalemate", 64, (0, 0))

        clock.tick(MAX_FPS)
        p.display.flip()


# Highlight square selected and moves for the piece selected
def HighlightSquares(screen, gs, validMoves, sqSelected):
    if sqSelected != ():
        r, c = sqSelected
        if gs.board[r][c][0] == ("w" if gs.whiteToMove else "b"):  # sqselected is a piece that can be moved:
            s = p.Surface((SQ_SIZE, SQ_SIZE))
            s.set_alpha(100)  # transparency value
            s.fill(p.Color("red"))
            screen.blit(s, (c * SQ_SIZE, r * SQ_SIZE))
            # highlight moves from that square
            s.fill(p.Color("yellow"))
            for move in validMoves:
                if move.startRow == r and move.startCol == c:
                    screen.blit(s, (move.endCol * SQ_SIZE, move.endRow * SQ_SIZE))
                    if move.isCapture and not move.isEnpassantMove:
                        screen.blit(IMAGES["CaptureSquare"], (move.endCol * SQ_SIZE, move.endRow * SQ_SIZE))


def ChangeMusic(music):
    '''global MUSIC
    if MUSIC != music:

        if music == 0:
            pygame.mixer.music.load("Chess/Gameplay.mp3")
        elif music == 1:
            pygame.mixer.music.load("Chess/InCheck.mp3")

        pygame.mixer.music.play(-1)
        MUSIC = music'''
    pass




# Responsible for all graphics in current game state
def DrawGameState(screen, gs, validMoves, sqSelected):
    screen.fill(p.Color("black"))
    DrawBoard(screen)  # draw squares on the board
    HighlightSquares(screen, gs, validMoves, sqSelected)  # highlighting of squares
    DrawPieces(screen, gs.board)  # draw pieces on top of the squares
    DrawMoveLog(screen, gs)


# Draws the squares on the board
def DrawBoard(screen):
    global colours
    colours = [p.Color("white"), p.Color("grey"), p.Color("black")]
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            color = colours[((r + c) % 2)]
            p.draw.rect(screen, color, p.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))

    grey = True
    for i in range(DIMENSION):
        txtSurface = FONTS[5].render(RANKS[i], True, colours[2])
        textLocation = p.Rect(0, 0, MOVE_LOG_PANEL_WIDTH, MOVE_LOG_PANEL_WIDTH)\
            .move(0, SQ_SIZE * i)
        screen.blit(txtSurface, textLocation)

        txtSurface = FONTS[5].render(FILES[i], True, colours[2])
        textLocation = p.Rect(0, 0, MOVE_LOG_PANEL_WIDTH, MOVE_LOG_PANEL_WIDTH)\
            .move(SQ_SIZE * (i+1) - txtSurface.get_width(), SQ_SIZE * DIMENSION - txtSurface.get_height())
        screen.blit(txtSurface, textLocation)

        grey = not grey

# Draws the pieces on the board from the current game state
def DrawPieces(screen, board):
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            piece = board[r][c]
            if piece != "--":
                screen.blit(IMAGES[piece], p.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))


def DrawCheckText(screen, gs, clock):
    kingPos = gs.whiteKingLocation if gs.whiteToMove else gs.blackKingLocation
    drawPos = (kingPos[1] * SQ_SIZE,
               kingPos[0] * SQ_SIZE + SQ_SIZE * 0.5)
    if kingPos[0] == 7:
        drawPos = (kingPos[1] * SQ_SIZE,
                   kingPos[0] * SQ_SIZE - SQ_SIZE * 0.5)

    txtSurface = BorderedText.Render("Check!", FONTS[4], p.Color("red"), p.Color("black"))
    txtLocation = p.Rect(0, 0, BOARD_WIDTH, BOARD_HEIGHT)\
        .move(drawPos[0] - txtSurface.get_width() / 2 + SQ_SIZE / 2,
              drawPos[1] - txtSurface.get_height() / 2 + SQ_SIZE / 2)


    for i in range(35):
        screen.fill(p.Color("black"))
        DrawBoard(screen)  # draw squares on the board
        DrawPieces(screen, gs.board)  # draw pieces on top of the squares
        DrawMoveLog(screen, gs)
        txtSurface.set_alpha(round(i * 7.3))
        screen.blit(txtSurface, txtLocation)
        pygame.display.flip()
        clock.tick(60)

    screen.fill(p.Color("black"))
    DrawBoard(screen)  # draw squares on the board
    DrawPieces(screen, gs.board)  # draw pieces on top of the squares
    DrawMoveLog(screen, gs)
    txtSurface.set_alpha(255)
    screen.blit(txtSurface, txtLocation)
    pygame.display.flip()

    for i in range(15):
        clock.tick(60)

    for i in range(15):
        screen.fill(p.Color("black"))
        DrawBoard(screen)  # draw squares on the board
        DrawPieces(screen, gs.board)  # draw pieces on top of the squares
        DrawMoveLog(screen, gs)
        txtSurface.set_alpha(255 - i * 17)
        screen.blit(txtSurface, txtLocation)
        pygame.display.flip()
        clock.tick(60)



def DrawMoveLog(screen, gs):
    txtSurface = BorderedText.Render("Chess", FONTS[0], p.Color("white"), (64, 64, 64))
    textLocation = p.Rect(0, 0, MOVE_LOG_PANEL_WIDTH, MOVE_LOG_PANEL_WIDTH)\
        .move(BOARD_WIDTH + MOVE_LOG_PANEL_WIDTH / 2 - txtSurface.get_width() / 2, 0)
    screen.blit(txtSurface, textLocation)

    txtSurface = BorderedText.Render("by Harrison McGrath", FONTS[1], p.Color("white"), (0, 0, 0))
    textLocation = p.Rect(0, 0, MOVE_LOG_PANEL_WIDTH, MOVE_LOG_PANEL_WIDTH)\
        .move(BOARD_WIDTH + MOVE_LOG_PANEL_WIDTH / 2 - txtSurface.get_width() / 2, 72 * TXT_MULTIPLIER)
    screen.blit(txtSurface, textLocation)

    txtSurface = FONTS[3].render("Press 'Z' to undo", True, p.Color("white"))
    textLocation = p.Rect(0, 0, MOVE_LOG_PANEL_WIDTH, MOVE_LOG_PANEL_WIDTH)\
        .move(BOARD_WIDTH + 10 * TXT_MULTIPLIER, 112 * TXT_MULTIPLIER)
    screen.blit(txtSurface, textLocation)
    txtSurface = FONTS[3].render("Press 'R' to reset", True, p.Color("white"))
    textLocation = p.Rect(0, 0, MOVE_LOG_PANEL_WIDTH, MOVE_LOG_PANEL_WIDTH) \
        .move(BOARD_WIDTH + 10 * TXT_MULTIPLIER, 137 * TXT_MULTIPLIER)
    screen.blit(txtSurface, textLocation)

    moveLogRect = p.Rect(BOARD_WIDTH, 0, MOVE_LOG_PANEL_WIDTH, MOVE_LOG_PANEL_HEIGHT)

    moveLog = gs.moveLog
    moveTexts = []
    for i in range(0, len(moveLog), 2):
        moveString = [f"{i//2 + 1}: {str(moveLog[i])}", ""]
        if i+1 < len(moveLog):
            moveString[1] = str(moveLog[i+1])
        moveTexts.append(moveString)

    if len(moveTexts) > 12:
        start = len(moveTexts) - 12
    else:
        start = 0

    padding = 8 * TXT_MULTIPLIER
    otherColumn = padding / 2 + MOVE_LOG_PANEL_WIDTH / 2.2
    textY = 172 * TXT_MULTIPLIER
    lineSpacing = 4 * TXT_MULTIPLIER
    for i in range(start, len(moveTexts)):
        text = moveTexts[i][0]
        textObject = FONTS[2].render(text, True, p.Color("white"))
        textLocation = moveLogRect.move(padding, textY)
        screen.blit(textObject, textLocation)

        text = moveTexts[i][1]
        textObject = FONTS[2].render(text, True, p.Color("white"))
        textLocation = moveLogRect.move(otherColumn, textY)
        screen.blit(textObject, textLocation)

        textY += textObject.get_height() + lineSpacing


def DrawAIThinking(screen, whiteToMove):
    DrawEndGameText(screen, " CPU is thinking... ", 40, offset=(0, 192 if not whiteToMove else -192),
                    background=True, colour="blue", borderColour="white")
    p.display.flip()


def AnimateMove(move, screen, board, clock, framesPerSquare=8):
    global colours
    deltaR = move.endRow - move.startRow
    deltaC = move.endCol - move.startCol
    frameCount = (abs(deltaR) + abs(deltaC)) * framesPerSquare
    for frame in range(frameCount + 1):
        r, c = (move.startRow + deltaR * frame / frameCount, move.startCol + deltaC * frame / frameCount)
        DrawBoard(screen)
        DrawPieces(screen, board)
        colour = colours[(move.endRow + move.endCol) % 2]
        endSquare = p.Rect(move.endCol * SQ_SIZE, move.endRow * SQ_SIZE, SQ_SIZE, SQ_SIZE)
        p.draw.rect(screen, colour, endSquare)
        if move.pieceCaptured != "--":
            if move.isEnpassantMove:
                enPassantRow = (move.endRow + 1) if move.pieceCaptured[0] == "b" else move.endRow - 1
                endSquare = p.Rect(move.endCol * SQ_SIZE, enPassantRow * SQ_SIZE, SQ_SIZE, SQ_SIZE)
            screen.blit(IMAGES[move.pieceCaptured], endSquare)
        # draw moving piece
        screen.blit(IMAGES[move.pieceMoved], p.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))
        p.display.flip()
        clock.tick(60)


def DrawEndGameText(screen, text, size, offset=(0, 0), background=True, colour="white", borderColour="black"):
    font = p.font.SysFont("Arial", round(size * TXT_MULTIPLIER), True, False)
    txtSurface = BorderedText.Render(text, font, p.Color(colour), p.Color(borderColour))

    textLocation = p.Rect(0, 0, BOARD_WIDTH, BOARD_HEIGHT).move(
        BOARD_WIDTH / 2 - txtSurface.get_width() / 2 - offset[0] * TXT_MULTIPLIER,
        BOARD_HEIGHT / 2 - txtSurface.get_height() / 2 - offset[1] * TXT_MULTIPLIER)

    if background:
        bg = p.Surface((txtSurface.get_width(), txtSurface.get_height()))
        bg.set_alpha(196)

        screen.blit(bg, (textLocation.x, textLocation.y))
    screen.blit(txtSurface, textLocation)


def GetGameType():
    # return (0, 5)

    types = ["1", "2", "3"]
    type = "4"

    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)

    while type not in types:
        os.system("cls")
        type = input('''Welcome to Chess!
    
Please enter game type. 

1: Human VS Human
2: Human VS Computer
3: Computer VS Computer

> ''')

    if type == "1":
        return (0, 0)
    elif type == "2":
        return (0, GetAIType(False))
    else:
        return (GetAIType(True), GetAIType(False))


def GetAIType(isWhite):
    os.system("cls")
    return int(input(f'''Please enter {"white" if isWhite else "black"} AI skill level.
    
Note: the higher the skill level, the smarter the move is but
it will take more time for it to generate the best move.

Skill level 1: Completely randomly picked moves
Skill level 2: Aggressive yet random
Skill level 3: Greedy Algorithm
Skill level 4: MinMax Algorithm
Skill level 5: NegaMax Algorithm

> '''))



if __name__ == "__main__":
    Main()
