#! -*- coding: utf-8 -*-
from abc import abstractmethod, ABCMeta
import copy

# Depth of the AI decision tree

THINKING_DEPTH = 4

# Define colors for pieces
class Color(object):
    BLACK = 1
    WHITE = 2
    EMPTY = 0

    @classmethod
    def invert(cls, color):
        """Invert the color (BLACK <-> WHITE) or keep EMPTY as is."""
        if color == cls.EMPTY:
            return color
        return cls.BLACK if color == cls.WHITE else cls.WHITE

# Chessboard class to manage the board and gameplay
class Chessboard(object):
    SPACE_COLOR_WHITE = 209
    #Light square color code
    SPACE_COLOR_BLACK = 94
    #Dark square color code

    board = None

    def fill(self):
        """Set up a starting position on the board."""
        board = self.board = [[EmptyCell() for x in range(8)] for y in range(8)]
        black = Color.BLACK
        white = Color.WHITE
        # FULL start position on the board
        # Place Black pieces (rank 8 and 7)
        board[0][0] = ChessmanRook(black)
        board[0][1] = ChessmanKnight(black)
        board[0][2] = ChessmanBishop(black)
        board[0][3] = ChessmanQueen(black)
        board[0][4] = ChessmanKing(black)
        board[0][5] = ChessmanBishop(black)
        board[0][6] = ChessmanKnight(black)
        board[0][7] = ChessmanRook(black)
        for x in range(8):
            board[1][x] = ChessmanPawn(black)

        # Place White pieces (rank 1 and 2)
        board[7][0] = ChessmanRook(white)
        board[7][1] = ChessmanKnight(white)
        board[7][2] = ChessmanBishop(white)
        board[7][3] = ChessmanQueen(white)
        board[7][4] = ChessmanKing(white)
        board[7][5] = ChessmanBishop(white)
        board[7][6] = ChessmanKnight(white)
        board[7][7] = ChessmanRook(white)
        for x in range(8):
            board[6][x] = ChessmanPawn(white)

        self.chessman_en_passant = None

    def get_king_pos(self, color):
        """Returns the position of a king of the color"""
        for x in range(8):
            for y in range(8):
                chessman = self.get_chessman(x, y)
                if chessman.color == color and chessman.CODE == ChessmanKing.CODE:
                    return [x, y]

    def is_check(self, king_pos, color):
        """Make sure if there is a check or no"""
        for x in range(8):
            for y in range(8):
                chessman = self.get_chessman(x, y)
                if chessman.color != Color.invert(color): continue
                if king_pos in chessman.get_moves(self, x, y):
                    return True
        return False

    def clone(self):
        """Create a deep copy of the chessboard."""
        cb = Chessboard()
        cb.board = copy.deepcopy(self.board)
        cb.chessman_en_passant = self.chessman_en_passant
        return cb

    def get_chessman(self, x, y):
        """Retrieve the chessman at the given coordinates."""
        return self.board[y][x]

    def get_color(self, x, y):
        """Get the color of the piece at the given coordinates."""
        return self.get_chessman(x, y).color

    def get_chessman_moves(self, x, y):
        """Get all valid moves for the chessman at the given position."""
        chessman = self.get_chessman(x, y)
        moves = chessman.get_moves(self, x, y)
        moves_final = list()
        for move in moves:
            self_clone = self.clone()
            self_clone.move_chessman((x, y), move)
            king_pos = self_clone.get_king_pos(chessman.color)
            if not self_clone.is_check(king_pos, chessman.color):
                moves_final.append(move)
        return moves_final

    def move_chessman(self, xy_from, xy_to):
        """Move a chessman from one position to another."""
        captured = (xy_to[1], xy_to[0])
        en_passant = self.chessman_en_passant

        # Remember if the move was appropriate for "en passant" on the next move
        self.define_en_passant(xy_from, xy_to)
        self.board[xy_to[1]][xy_to[0]] = self.board[xy_from[1]][xy_from[0]]

        # If it's the rook/King, they can't make a Castling anymore
        if self.board[xy_to[1]][xy_to[0]].CODE in (ChessmanKing.CODE, ChessmanRook.CODE):
            self.board[xy_to[1]][xy_to[0]].not_moved = False

        # Make the "en passant" movement
        if en_passant is None: pass
        elif (xy_to[1] + (1 if self.board[xy_to[1]][xy_to[0]].color == Color.WHITE else -1),
              xy_to[0]) \
                == (en_passant[1], en_passant[0]):
            captured = (en_passant[1], en_passant[0])
            self.board[captured[0]][captured[1]] = EmptyCell()

        self.board[xy_from[1]][xy_from[0]] = EmptyCell()

        # If it's rooking, make sure to move the rook too
        if self.board[xy_to[1]][xy_to[0]].CODE == ChessmanKing.CODE:
            if xy_to[0] - xy_from[0] in (2, -2):
                return (captured[1], captured[0]), True

        return (captured[1], captured[0]), False

    def define_en_passant(self, xy_from, xy_to):
        if not self.get_chessman(xy_from[0], xy_from[1]).CODE == ChessmanPawn.CODE:
            self.chessman_en_passant = None
            return
        if not (xy_to[1] - xy_from[1]) * (
                -1 if self.get_chessman(xy_from[0], xy_from[1]).color == Color.WHITE
                else 1) == 2:
            self.chessman_en_passant = None
            return
        self.chessman_en_passant = xy_to

    def is_empty(self, x, y):
        """Check if a cell on the board is empty."""
        return self.get_chessman(x, y).CODE == 'empty'

    def rate(self, color):
        """Evaluate the board for a given color."""
        res = 0
        pawn_x_position = []
        for y in range(8):
            for x in range(8):
                if self.get_color(x, y) != color:
                    continue
                chessman = self.get_chessman(x, y)
                res += chessman.rate(self, x, y)
                if chessman.CODE == 'pawn':
                    pawn_x_position.append(x)
        # double pawns reduce the rate
        p = pawn_x_position
        res += 2 * (len(set(p)) - len(p))
        # alone pawn reduce the rate
        for i in range(1, 6):
            if i in p and (i-1) not in p and (i+1) not in p:
                res -= 2
        return res

    def __str__(self):
        """Return the board's string representation."""
        res = "  a b c d e f g h\n"
        for y in range(8):
            res += f"{8 - y} "  # Row numbers
            for x in range(8):
                color = self.SPACE_COLOR_BLACK if (x + y) % 2 else self.SPACE_COLOR_WHITE
                res += f'\033[48;5;{color}m{self.board[y][x]} '
            res += "\033[0m\n"
        return res

# Define an empty cell
class EmptyCell(object):
    CODE = 'empty'
    color = Color.EMPTY

    def get_moves(self, board, x, y):
        raise Exception('Error!')

    def rate(self, board, x, y):
        raise Exception('Error!')

    def __str__(self):
        return ' '

# Abstract class for chess pieces
class Chessman(object):
    __metaclass__ = ABCMeta

    CODE = None
    VALUE = None
    WHITE_IMG = None
    BLACK_IMG = None

    color = None

    def __init__(self, color):
        self.color = color

    @abstractmethod
    def get_possible_moves(self, board: Chessboard, x, y):
        return []

    @abstractmethod
    def rate(self, board: Chessboard, x, y):
        return 0

    @abstractmethod
    def get_moves(self, board, x, y):
        return []

    def get_legal_moves(self, board, x, y):
        chessman = board.get_chessman(x, y)
        moves = chessman.get_moves(board, x, y, castling=True) \
            if chessman.CODE == ChessmanKing.CODE else \
            chessman.get_moves(board, x, y)

        moves_final = list()
        for move in moves:
            self_clone = board.clone()
            self_clone.move_chessman((x, y), move)
            king_pos = self_clone.get_king_pos(chessman.color)
            if not self_clone.is_check(king_pos, chessman.color):
                moves_final.append(move)
        return moves_final

    def enemy_color(self):
        """Return the color of the enemy."""
        return Color.invert(self.color)

    def __str__(self):
        return self.WHITE_IMG if self.color == Color.WHITE else self.BLACK_IMG

#PAWN
class ChessmanPawn(Chessman):
    CODE = 'pawn'
    VALUE = 10
    WHITE_IMG = '♙'
    BLACK_IMG = '♟'

    def get_possible_moves(self, board: Chessboard, x, y):
        moves = []
        y += -1 if self.color == Color.WHITE else 1
        if y == -1 or y == 8:
            return moves
        if x > 0:
            moves.append([x - 1, y])
        if x < 7:
            moves.append([x + 1, y])
        moves.append([x, y])
        if self.color == Color.WHITE and y == 5:
            moves.append([x, y - 1])
        if self.color == Color.BLACK and y == 2:
            moves.append([x, y + 1])
        return moves

    def get_moves(self, board: Chessboard, x, y):
        moves = []
        y += -1 if self.color == Color.WHITE else 1
        if y == -1 or y == 8:
            return moves
        if x > 0 and (board.get_color(x-1, y) == self.enemy_color()
                      or board.chessman_en_passant == (x-1, y+(1 if self.color == Color.WHITE else -1))):
            moves.append([x-1, y])
        if x < 7 and (board.get_color(x+1, y) == self.enemy_color()
                      or board.chessman_en_passant == (x+1, y+(1 if self.color == Color.WHITE else -1))):
            moves.append([x+1, y])
        if board.is_empty(x, y):
            moves.append([x, y])
            if self.color == Color.WHITE and y == 5 and board.is_empty(x, y-1):
                moves.append([x, y-1])
            if self.color == Color.BLACK and y == 2 and board.is_empty(x, y+1):
                moves.append([x, y+1])
        return moves

    def rate(self, board: Chessboard, x, y):
        return self.VALUE + 1 * (8-y if self.color == Color.WHITE else y)

#KING
class ChessmanKing(Chessman):
    CODE = 'king'
    VALUE = 0
    WHITE_IMG = '♔'
    BLACK_IMG = '♚'
    not_moved = True

    def get_possible_moves(self, board: Chessboard, x, y):
        moves = []
        for j in (y-1, y, y+1):
            for i in (x-1, x, x+1):
                if i == x and j == y:
                    continue
                if 0 <= i <= 7 and 0 <= j <= 7:
                    moves.append([i, j])
        return moves

    def get_moves(self, board, x, y, castling=None):
        moves = []
        for j in (y-1, y, y+1):
            for i in (x-1, x, x+1):
                if i == x and j == y:
                    continue
                if 0 <= i <= 7 and 0 <= j <= 7 and board.get_color(i, j) != self.color:
                    moves.append([i, j])
        # Castling
        if castling is not None:
            if self.not_moved:
                # Short
                if      not board.is_check([4, y], board.get_color(x, y)) and \
                        not board.is_check([5, y], board.get_color(x, y)) and \
                        all([board.get_color(*cell) == Color.EMPTY for cell in ([5, y], [6, y])]) and \
                        board.get_chessman(7, y).CODE == ChessmanRook.CODE:
                    if board.get_chessman(7, y).not_moved:
                        moves.append([6, y])
                # Long
                if      not board.is_check([4, y], board.get_color(x, y)) and \
                        not board.is_check([3, y], board.get_color(x, y)) and \
                        all([board.get_color(*cell) == Color.EMPTY for cell in ([3, y], [2, y], [1, y])]) and \
                        board.get_chessman(0, y).CODE == ChessmanRook.CODE:
                    if board.get_chessman(0, y).not_moved:
                        moves.append([2, y])
        return moves

    def rate(self, board, x, y):
        return self.VALUE

#ROOK
class ChessmanRook(Chessman):
    CODE = 'rook'
    VALUE = 50
    WHITE_IMG = '♖'
    BLACK_IMG = '♜'
    not_moved = True

    def get_possible_moves(self, board: Chessboard, x, y):
        moves = []
        for j in (-1, 1):
            i = x + j
            while 0 <= i <= 7:
                moves.append([i, y])
                i += j
        for j in (-1, 1):
            i = y + j
            while 0 <= i <= 7:
                moves.append([x, i])
                i += j
        return moves

    def get_moves(self, board, x, y):
        moves = []
        for j in (-1, 1):
            i = x + j
            while 0 <= i <= 7:
                color = board.get_color(i, y)
                if color == self.color:
                    break
                moves.append([i, y])
                if color != Color.EMPTY:
                    break
                i += j
        for j in (-1, 1):
            i = y + j
            while 0 <= i <= 7:
                color = board.get_color(x, i)
                if color == self.color:
                    break
                moves.append([x, i])
                if color != Color.EMPTY:
                    break
                i += j
        return moves

    def rate(self, board, x, y):
        return self.VALUE

#BISHOP
class ChessmanBishop(Chessman):
    CODE = 'bishop'
    VALUE = 30
    WHITE_IMG = '♗'
    BLACK_IMG = '♝'

    def get_possible_moves(self, board, x, y):
        moves = []
        # Diagonal directions: (dx, dy) pairs
        directions = [(-1, -1), (1, -1), (-1, 1), (1, 1)]

        for dx, dy in directions:
            i, j = x + dx, y + dy  # Move diagonally in the current direction
            while 0 <= i <= 7 and 0 <= j <= 7:  # Stay within board boundaries
                moves.append([i, j])  # Add the valid move
                i += dx  # Continue in the same diagonal direction
                j += dy
        return moves

    def get_moves(self, board, x, y):
        moves = []
        # Diagonal directions: (dx, dy) pairs
        directions = [(-1, -1), (1, -1), (-1, 1), (1, 1)]

        for dx, dy in directions:
            i, j = x + dx, y + dy  # Move diagonally in the current direction
            while 0 <= i <= 7 and 0 <= j <= 7:  # Stay within board boundaries
                color = board.get_color(i, j)  # Get the color at the current position
                if color == self.color:  # Stop if the position has a friendly piece
                    break
                moves.append([i, j])  # Add the valid move
                if color != Color.EMPTY:  # Stop if the position has an enemy piece
                    break
                i += dx  # Continue in the same diagonal direction
                j += dy
        return moves

#QUEEN
class ChessmanQueen(Chessman):
    CODE = 'queen'
    VALUE = 90
    WHITE_IMG = '♕'
    BLACK_IMG = '♛'

    def get_possible_moves(self, board, x, y):
        moves = []
        # All 8 possible directions: (dx, dy) pairs
        directions = [
            (-1, 0), (1, 0),  # Left, Right (Horizontal)
            (0, -1), (0, 1),  # Up, Down (Vertical)
            (-1, -1), (1, -1), (-1, 1), (1, 1)  # Diagonals: Top-Left, Top-Right, Bottom-Left, Bottom-Right
        ]

        for dx, dy in directions:
            i, j = x + dx, y + dy  # Move in the current direction
            while 0 <= i <= 7 and 0 <= j <= 7:  # Stay within board boundaries
                moves.append([i, j])  # Add the valid move
                i += dx  # Continue in the same direction
                j += dy
        return moves

    def get_moves(self, board, x, y):
        moves = []
        # All 8 possible directions: (dx, dy) pairs
        directions = [
            (-1, 0), (1, 0),  # Left, Right (Horizontal)
            (0, -1), (0, 1),  # Up, Down (Vertical)
            (-1, -1), (1, -1), (-1, 1), (1, 1)  # Diagonals: Top-Left, Top-Right, Bottom-Left, Bottom-Right
        ]

        for dx, dy in directions:
            i, j = x + dx, y + dy  # Move in the current direction
            while 0 <= i <= 7 and 0 <= j <= 7:  # Stay within board boundaries
                color = board.get_color(i, j)  # Get the color at the current position
                if color == self.color:  # Stop if the position has a friendly piece
                    break
                moves.append([i, j])  # Add the valid move
                if color != Color.EMPTY:  # Stop if the position has an enemy piece
                    break
                i += dx  # Continue in the same direction
                j += dy
        return moves

#KNIGHT
class ChessmanKnight(Chessman):
    CODE = 'knight'
    VALUE = 30
    WHITE_IMG = '♘'
    BLACK_IMG = '♞'

    def get_possible_moves(self, board, x, y):
        moves = []
        # All 8 possible "L" shaped moves for the Knight
        knight_moves = [
            (-2, -1), (-2, 1),  # Up-Left, Up-Right
            (-1, -2), (-1, 2),  # Left-Up, Right-Up
            (1, -2), (1, 2),    # Left-Down, Right-Down
            (2, -1), (2, 1)     # Down-Left, Down-Right
        ]

        for dx, dy in knight_moves:
            i, j = x + dx, y + dy  # New position after the move
            if 0 <= i <= 7 and 0 <= j <= 7:  # Check board boundaries
                color = board.get_color(i, j)  # Get the color at the new position
        return moves

    def get_moves(self, board, x, y):
        moves = []
        # All 8 possible "L" shaped moves for the Knight
        knight_moves = [
            (-2, -1), (-2, 1),  # Up-Left, Up-Right
            (-1, -2), (-1, 2),  # Left-Up, Right-Up
            (1, -2), (1, 2),    # Left-Down, Right-Down
            (2, -1), (2, 1)     # Down-Left, Down-Right
        ]

        for dx, dy in knight_moves:
            i, j = x + dx, y + dy  # New position after the move
            if 0 <= i <= 7 and 0 <= j <= 7:  # Check board boundaries
                color = board.get_color(i, j)  # Get the color at the new position
                if color != self.color:  # Valid if the position is empty or contains an enemy piece
                    moves.append([i, j])
        return moves


class AI(object):
    def __init__(self, my_color, depth):
        self.my_color = my_color
        self.enemy_color = Color.invert(my_color)
        self.depth = depth

    def do(self, board, depth=0):
        enemy = bool(depth % 2)
        color = self.enemy_color if enemy else self.my_color
        if depth == self.depth:
            return board.rate(self.my_color) - board.rate(self.enemy_color)*1.1
        rates = []
        for y in range(8):
            for x in range(8):
                if board.get_color(x, y) != color:
                    continue
                xy_from = [x, y]
                for xy_to in board.get_chessman_moves(x, y):
                    new_board = board.clone()
                    target_cell = new_board.move_chessman(xy_from, xy_to)
                    captured = target_cell.CODE != 'empty'
                    if captured and target_cell.CODE == 'king':
                        rate = -1000 if enemy else 1000  # king capturing
                    else:
                        rate = self.do(new_board, depth + 1)
                        if rate is None:
                            continue
                        if captured and not enemy:
                            rate += self.depth - depth  # a little more aggression
                    if depth:
                        rates.append(rate)
                    else:
                        rates.append([rate, xy_from, xy_to])
        if not depth:
            return rates
        if not rates:
            return None
        rate = min(rates) if enemy else max(rates)
        return rate


class Game(object):
    @staticmethod
    def clear_screen():
        print("\033[2J\033[1;3H\033[14;0m")

    def __init__(self):
        cb = Chessboard()
        cb.fill()

        self.clear_screen()
        print(cb)

        color = Color.WHITE
        for i in range(22):
            max_rate = -9999
            xy_from = xy_to = None
            rates = AI(color, THINKING_DEPTH).do(cb)
            for rate in rates:
                if rate[0] < max_rate:
                    continue
                max_rate, xy_from, xy_to = rate
            if not xy_from:
                print('end')
                exit()
            cb.move_chessman(xy_from, xy_to)
            color = Color.invert(color)
            self.clear_screen()
            print(cb)


if __name__ == "__main__":
    Game()
