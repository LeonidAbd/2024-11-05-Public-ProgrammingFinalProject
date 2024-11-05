from __future__ import annotations

Mask = int

class PieceType:
    WHITE = 0       #      1
    BLACK = 2       #     10
    ANY_COLOR = 3   #     11
    PAWN = 4 + 3    #   1 11
    KNIGHT = 8 + 3  #  10 11
    BISHOP = 12 + 3 #  11 11
    ROOK = 16 + 3   # 100 11
    QUEEN = 20 + 3  # 101 11
    KING = 24 + 3   # 110 11


def format_mask(mask: Mask) -> str:
    string_mask: str = bin(mask)[2:][::-1]
    string_mask += "0" * (64 - len(string_mask))
    res: str = ""
    for i in range(8):
        res1 = ""
        for e in string_mask[i * 8:i * 8 + 8]:
            if e == "0":
                res += ". "
            else:
                res1 += e + " "
        res = res1 + "\n" + res
    return res[:-1]


def print_mask(mask: Mask) -> None:
    print(format_mask(mask))


class ChessEngine:
    _mask_white_pieces: Mask
    _mask_black_pieces: Mask  # maybe it's not needed, can be deleted in the future
    _mask_pawns: Mask
    _mask_knights: Mask
    _mask_bishops: Mask
    _mask_rooks: Mask
    _mask_queens: Mask
    _mask_kings: Mask
    _mask_pieces_moved: Mask  # needed for castling
    _white_turn: bool

    def __init__(self):
        pass  # define all the masks

    def get_pieces(self, piece_type):
        pass  # return the pieces by selecting the type, for example: "wK" - white knight

    def select_piece(self, mask: Mask):
        pass  # return True if the piece can be picked, otherwise return False
