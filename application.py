# import tkinter  # some gui library
from chessengine import *


class Application:
    _chess_engine: ChessEngine

    def __init__(self):
        self._chess_engine = ChessEngine()

    def run(self):
        print(self)

    def __str__(self):
        return ("Application object {\n" +
                f"    ChessEngine: {ChessEngine},\n" +
                "}")
