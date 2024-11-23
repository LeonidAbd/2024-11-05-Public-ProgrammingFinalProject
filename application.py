import tkinter
from chess_engine import *


class Application:
    _chess_engine: ChessEngine
    _window: tkinter.Tk

    def __init__(self):
        self._chess_engine = ChessEngine()
        self._window = tkinter.Tk()

    def run(self):
        # self.show_main_menu_scene()
        # self.show_game_scene()
        self._window.mainloop()

    def __str__(self):
        return ("Application object {\n" +
                f"    ChessEngine: {ChessEngine},\n" +
                "}")

    def _get_piece(self, piece_type):
        self._chess_engine.get_pieces(piece_type)
