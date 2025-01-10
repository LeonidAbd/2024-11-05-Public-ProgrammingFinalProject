from __future__ import annotations

import copy
import json
import math

import flet
import flet.canvas
from typing import Callable
import pynput

import testfilechess
from chess_engine import *


class Application:
    class Settings:
        board_two_sided_indexing: bool

        def __init__(self, filename):
            settings_json = json.load(open(filename, "r"))
            for key, value in settings_json.items():
                self.__setattr__(key, value["value"])

    class Scene:
        CONTENT_WHEN_DRAGGING_OPACITY: int = 0.5

        class _Cell(flet.DragTarget):
            i: int; j: int
            active: bool
            color_saved: str; content: flet.Container; id_accept: int
            _scene_self: Application.Scene | None = None
            
            @staticmethod
            def set_scene_self(scene: Application.Scene):
                Application.Scene._Cell._scene_self = scene

            def set_bgc(self, bgc: str):
                self.content.bgcolor = bgc
                self.content.border = flet.border.all(0, bgc)

            def get_bgc_inactive(self):
                return "#B0B0B0" if (self.i + self.j) % 2 == 0 else "#E0E0E0"

            def get_bgc_active(self):
                return "#84B09A" if (self.i + self.j) % 2 == 0 else "#A6DEC2"

            def get_bgc_possible_moves(self):
                return "#8D9EB0" if (self.i + self.j) % 2 == 0 else "#B1C8DE"

            def get_bgc_premove(self):
                return "#B0B096" if (self.i + self.j) % 2 == 0 else "#DEDEBD"

            def save_color(self):
                self.color_saved = self.content.bgcolor

            @staticmethod
            def get_cell(i, j) -> Application.Scene._Cell:
                return Application.Scene._Cell._scene_self.board_cells.controls[7 - i].controls[j]

        class _Piece(flet.Draggable):
            content_feedback_saved: flet.Image; ij: tuple[int, int]; id: int
            active: int
            # 0 - inactive
            # 1 - active
            # 2 - active after dropping
            # 3 - dropped
            # 4 - dropped out of board
            selected: bool
            board_piece: testfilechess.Chessman

            def is_active(self):
                return self.active in (1, 2)

        class _BoardStack(flet.Stack):
            _scene: Application.Scene | None

            @staticmethod
            def set_scene_self(scene: Application.Scene):
                Application.Scene._BoardStack._scene = scene

            class Layer(flet.canvas.Canvas):
                ij1: tuple[int, int]
                ij2: tuple[int, int] | None

                color_free = "#378A8A"
                color_constant = "#36618E"

                def line_update(self, ij2: tuple[int, int]):
                    self.ij2 = ij2
                    cell_size = Application.Scene._BoardStack._scene.cell_size
                    x1 = cell_size * 80 + cell_size / 2 * (1 + 2 * self.ij1[1])
                    y1 = cell_size * 80 + cell_size / 2 * (15 - 2 * self.ij1[0])
                    x2 = cell_size * 80 + cell_size / 2 * (1 + 2 * self.ij2[1])
                    y2 = cell_size * 80 + cell_size / 2 * (15 - 2 * self.ij2[0])
                    angle = math.atan((y2 - y1) / (x2 - x1)) + (0 if x2 > x1 else math.pi) \
                        if x2 != x1 else math.pi * 0.5 if y2 > y1 else -math.pi * 0.5
                    print(x2-x1, y2-y1, angle)
                    self.shapes = [
                        flet.canvas.Path([
                            flet.canvas.Path.MoveTo(x1 + cell_size * 0.4, y1),
                            flet.canvas.Path.ArcTo(x1, y1 + cell_size * 0.4, radius=cell_size * 0.4),
                            flet.canvas.Path.ArcTo(x1 - cell_size * 0.4, y1, radius=cell_size * 0.4),
                            flet.canvas.Path.ArcTo(x1, y1 - cell_size * 0.4, radius=cell_size * 0.4),
                            flet.canvas.Path.ArcTo(x1 + cell_size * 0.4, y1, radius=cell_size * 0.4),
                        ],

                            paint=flet.Paint(stroke_width=5, color=self.color_free, style=flet.PaintingStyle.STROKE),)
                    ] \
                        if self.ij1 == self.ij2 else \
                        [
                        flet.canvas.Line(
                            x1=x1,
                            y1=y1,
                            x2=x2 + cell_size * 0.3 * math.cos(angle) * (-1),
                            y2=y2 + cell_size * 0.3 * math.sin(angle) * (-1),
                            paint=flet.Paint(stroke_width=5, color=self.color_free, stroke_cap=flet.StrokeCap.ROUND),
                        ),
                        flet.canvas.Path([
                                flet.canvas.Path.MoveTo(x2 + cell_size * 0.1 * math.cos(angle),
                                                        y2 + cell_size * 0.1 * math.sin(angle)),
                                flet.canvas.Path.LineTo(x2 + cell_size * 0.4 * math.cos((angle + math.pi * 0.8)),
                                                        y2 + cell_size * 0.4 * math.sin((angle + math.pi * 0.8))),
                                flet.canvas.Path.LineTo(x2 + cell_size * 0.4 * math.cos((angle + math.pi * 1.2)),
                                                        y2 + cell_size * 0.4 * math.sin((angle + math.pi * 1.2))),
                                flet.canvas.Path.LineTo(x2 + cell_size * 0.1 * math.cos(angle),
                                                        y2 + cell_size * 0.1 * math.sin(angle)),
                        ],
                            paint=flet.Paint(stroke_width=5, color=self.color_free, style=flet.PaintingStyle.FILL),
                        )
                    ]
                    self.update()

            _scene: Application.Scene | None
            _free_layer: Application.Scene._BoardStack.Layer | None = None
            _last_combination = 0

            def new_free_layer(self, ij1: tuple[int, int]):
                if not self.free_layer_is_none(): return
                free_layer = Application.Scene._BoardStack.Layer(shapes=[
                ], top=0, left=0, opacity=0.7,
                    width=Application.Scene._BoardStack._scene.cell_size * 8, height=Application.Scene._BoardStack._scene.cell_size * 8,
                    offset=(-10, -10))
                free_layer.ij1 = ij1
                self.free_layer_set(free_layer)
                free_layer.line_update(ij1)

            def free_layer_update(self, ij2: tuple[int, int]):
                if self.free_layer_is_none(): return
                self._free_layer: Application.Scene._BoardStack.Layer
                self._free_layer.line_update(ij2)

            def free_layer_set(self, free_layer: Layer):
                if self.free_layer_is_none():
                    self.controls.append(None)
                self._free_layer = free_layer
                self.controls[-1] = free_layer
                self.update()

            def free_layer_is_none(self) -> None:
                if not hasattr(self, "_free_layer"):
                    self._free_layer = None
                return self._free_layer is None

            def free_layer_delete(self):
                if self.free_layer_is_none(): return
                if len(self.controls) > 1:
                    self.controls.pop(-1)
                self._free_layer = None

            def free_layer_hide(self):
                if not self.free_layer_is_none():
                    self._free_layer.opacity = 0

            def free_layer_show(self):
                if not self.free_layer_is_none():
                    self._free_layer.opacity = 0.7

            def free_layer_is_hidden(self):
                if self.free_layer_is_none(): return
                return self._free_layer.opacity <= 0

            def free_layer_save(self):
                if self.free_layer_is_none(): return
                for layer in self.controls[1:-1]:
                    if self._free_layer.ij1 == layer.ij1 and self._free_layer.ij2 == layer.ij2:
                        self.controls.remove(layer)
                        print(self._free_layer)
                        self.free_layer_delete()
                        self.update()
                        return
                self._free_layer.opacity = 0.5
                for shape in self._free_layer.shapes:
                    shape.paint.color = self._free_layer.color_constant
                self._free_layer = None
                self.update()

            def clear(self):
                self.controls = [self.controls[0]]
                self._free_layer = None
                self.update()

        _application: Application
        _app_function: Callable[[flet.Page], None]
        _page: flet.Page
        pieces: list[Application.Scene._Piece]
        cell_size: int

        def __init__(self, application: Application, size: tuple[int, int] = (800, 600)):
            def app_function(page: flet.Page):
                self._page = page
                page.window.width = self._window_width
                page.window.height = self._window_height
                self._show_scene_mainmenu()

            self._window_width = size[0]
            self._window_height = size[1]
            self._application = application
            self._app_function = app_function

        def run(self):
            flet.app(self._app_function)

        # def _add_menu_bar(self):
        #     def save_file(file_name: str):
        #         print(file_name)
        #
        #     save_dialog = flet.AlertDialog(
        #         modal=True,
        #         content=flet.Text("Save modal dialog"),
        #         title=flet.Text("Save"),
        #         on_dismiss=lambda _: self._page.close(save_dialog),
        #         actions=[
        #             saving_name := flet.TextField(on_click=lambda _: None, suffix_text=(saving_suffix := ".chess.json"),
        #                                           on_submit=lambda _: [self._page.close(save_dialog),
        #                                                                save_file(saving_name.value + saving_suffix)]),
        #             flet.TextButton("Save", on_click=lambda _: [self._page.close(save_dialog),
        #                                                         save_file(saving_name.value + saving_suffix)]),
        #             flet.TextButton("Cancel", on_click=lambda _: self._page.close(save_dialog)),
        #         ]
        #     )
        #
        #     open_button = flet.MenuItemButton(
        #         height=30,
        #         content=flet.Text("Open", font_family="Arial", weight=flet.FontWeight.W_500, size=15),
        #         style=flet.ButtonStyle(bgcolor={flet.ControlState.HOVERED: "#E0E0E0"},
        #                                shape=flet.RoundedRectangleBorder(radius=5)),
        #         # on_click=lambda _: None,
        #     )
        #     save_button = flet.MenuItemButton(
        #         height=30,
        #         content=flet.Text("Save", font_family="Arial", weight=flet.FontWeight.W_500, size=15),
        #         style=flet.ButtonStyle(bgcolor={flet.ControlState.HOVERED: "#E0E0E0"},
        #                                shape=flet.RoundedRectangleBorder(radius=5)),
        #         on_click=lambda _: self._page.open(save_dialog),
        #     )
        #     menu_bar = flet.MenuBar(
        #         controls=[
        #             flet.SubmenuButton(
        #                 content=flet.Text("File", font_family="Arial", weight=flet.FontWeight.W_600, size=15),
        #                 controls=[open_button, save_button]
        #             ),
        #         ],
        #     )
        #     self._page.controls.append(menu_bar)

        def _add_scene_mainmenu(self):
            # self._add_menu_bar()

            title_label = flet.Row(controls=[
                flet.Container(width=60),
                flet.Text("Classic Chess", weight=flet.FontWeight.W_700, size=60)
            ])

            def newgame_call(_):
                for main_button in main_column.controls:
                    main_button.disabled = True

                value_dict = {True: "Player", False: "PC", None: "Random"}

                def set_player(id: int):
                    self._application.change_player(id)
                    player_button_0.content.value = value_dict[self._application._players[0]]
                    player_button_1.content.value = value_dict[self._application._players[1]]
                    update_pc_difficulty()
                    self._page.update()

                additional_column.controls.extend([
                    flet.Row([
                        flet.Container(width=30),
                        flet.Text("Sides:", weight=flet.FontWeight.W_600, size=40)
                    ]),
                    player_row_0 := flet.Row([
                        flet.Text("White:", width=50),
                        player_button_0 := flet.Button(
                            content=flet.Text(value_dict[self._application._players[0]]),
                            on_click=lambda _: set_player(0),
                            width=60,
                            style=flet.ButtonStyle(shape=flet.RoundedRectangleBorder(radius=7)),
                        ),
                    ]),
                    player_row_1 := flet.Row([
                        flet.Text("Black:", width=50),
                        player_button_1 := flet.Button(
                            content=flet.Text(value_dict[self._application._players[1]]),
                            on_click=lambda _: set_player(1),
                            width=60,
                            style=flet.ButtonStyle(shape=flet.RoundedRectangleBorder(radius=7)),
                        ),
                    ]),
                    flet.Row([
                        flet.Button(
                            content=flet.Text("Start Game"),
                            on_click=lambda _: self._show_scene_chess(),
                            width=100,
                            style=flet.ButtonStyle(
                                shape=flet.RoundedRectangleBorder(radius=9),
                                color="#FFFFFF",
                                bgcolor="#3978A8",  # 36618E
                            ),
                        ),
                        flet.Button(
                            content=flet.Text("Cancel"),
                            on_click=newgame_cancel,
                            width=70,
                            style=flet.ButtonStyle(shape=flet.RoundedRectangleBorder(radius=9)),
                        ),
                    ])
                ])

                def add_pc_difficulty(*ids: list[int]):
                    def change_value(event: flet.ControlEvent):
                        self._application._pc_difficulty = self._application._pc_difficulty % \
                                                            self._application._pc_difficulty_max + 1
                        event.control.content.value = str(self._application._pc_difficulty)
                        self._page.update()

                    for id, player_row in {0: player_row_0, 1: player_row_1}.items():
                        if id in ids and len(player_row.controls) < 3:
                            player_row.controls.append(flet.Button(
                                content=flet.Text(str(self._application._pc_difficulty)),
                                on_click=change_value,
                                width=50,
                                style=flet.ButtonStyle(shape=flet.RoundedRectangleBorder(radius=7)),
                            ))
                        if id not in ids and len(player_row.controls) >= 3:
                            player_row.controls.pop(2)

                update_pc_difficulty = lambda: add_pc_difficulty(*[i
                                                                   for i in range(len(self._application._players))
                                                                   if not self._application._players[i]])
                update_pc_difficulty()

                self._page.update()

            def newgame_cancel(_):
                for main_button in main_column.controls:
                    main_button.disabled = False
                additional_column.controls.clear()
                self._page.update()

            def loadgame_call(_):
                for main_button in main_column.controls:
                    main_button.disabled = True

                def press_checkbox(event: flet.ControlEvent):
                    if not event.control.value:
                        start_game_button.disabled = True
                    else:
                        start_game_button.disabled = False
                        for checkbox in checkboxes.controls:
                            checkbox.value = False
                        event.control.value = True
                    self._page.update()

                save_label_padding = (2, 6, 2, 0)

                additional_column.controls.extend([
                    flet.Row([
                        flet.Container(width=10),
                        flet.Text("Load Game:", weight=flet.FontWeight.W_600, size=30)
                    ]),
                    flet.Row([
                        flet.Container(width=30),
                        flet.Container(
                            content=flet.Row(controls=[
                                flet.Container(width=save_label_padding[3]),
                                flet.Column(controls=[
                                    flet.Container(height=save_label_padding[0]),
                                    checkboxes := flet.Column(controls=[
                                        flet.Checkbox(label="Game #1", on_change=press_checkbox, shape=flet.StadiumBorder()),
                                        flet.Checkbox(label="Game #2", on_change=press_checkbox, shape=flet.StadiumBorder()),
                                        flet.Checkbox(label="Game #3", on_change=press_checkbox, shape=flet.StadiumBorder()),
                                        flet.Checkbox(label="Game #4", on_change=press_checkbox, shape=flet.StadiumBorder()),
                                    ]),
                                    flet.Container(height=save_label_padding[2]),
                                ]),
                                flet.Container(width=save_label_padding[1]),
                            ]),
                            border=flet.border.all(3, "#36618E"),
                        ),
                    ]),
                    flet.Row([
                        start_game_button := flet.Button(
                            disabled=True,
                            content=flet.Text("Start Game"),
                            on_click=lambda _: print("START LOADED GAME"),
                            width=100,
                            style=flet.ButtonStyle(
                                shape=flet.RoundedRectangleBorder(radius=9),
                                color="#FFFFFF",
                                bgcolor={flet.ControlState.DISABLED: "#8C8C8C", flet.ControlState.DEFAULT: "#3978A8"},
                            ),
                        ),
                        flet.Button(
                            content=flet.Text("Cancel"),
                            on_click=loadgame_cancel,
                            width=70,
                            style=flet.ButtonStyle(shape=flet.RoundedRectangleBorder(radius=9)),
                        ),
                    ]),
                ])
                self._page.update()

            def loadgame_cancel(_):
                return newgame_cancel(_)

            def settings_call(_):
                for main_button in main_column.controls:
                    main_button.disabled = True

                settings_label_padding = (2, 6, 2, 0)

                additional_column.controls.extend([
                    flet.Row([
                        flet.Container(width=10),
                        flet.Text("Settings:", weight=flet.FontWeight.W_600, size=30)
                    ]),
                    flet.Row([
                        flet.Container(width=30),
                        flet.Container(
                            content=flet.Row(controls=[
                                flet.Container(width=settings_label_padding[3]),
                                flet.Column(controls=[
                                    flet.Container(height=settings_label_padding[0]),

                                    flet.Container(height=settings_label_padding[2]),
                                ]),
                                flet.Container(width=settings_label_padding[1]),
                            ]),
                            border=flet.border.all(3, "#36618E"),
                        ),
                    ]),
                    flet.Row([
                        start_game_button := flet.Button(
                            disabled=True,
                            content=flet.Text("OK"),
                            on_click=lambda _: [print("APPLY SETTINGS"), settings_cancel(_)],
                            width=100,
                            style=flet.ButtonStyle(
                                shape=flet.RoundedRectangleBorder(radius=9),
                                color="#FFFFFF",
                                bgcolor={flet.ControlState.DISABLED: "#8C8C8C", flet.ControlState.DEFAULT: "#3978A8"},
                            ),
                        ),
                        flet.Button(
                            content=flet.Text("Cancel"),
                            on_click=settings_cancel,
                            width=70,
                            style=flet.ButtonStyle(shape=flet.RoundedRectangleBorder(radius=9)),
                        ),
                        flet.Button(
                            disabled=True,
                            content=flet.Text("Apply"),
                            on_click=lambda _: print("APPLY SETTINGS"),
                            width=100,
                            style=flet.ButtonStyle(
                                shape=flet.RoundedRectangleBorder(radius=9),
                                color="#FFFFFF",
                                bgcolor={flet.ControlState.DISABLED: "#8C8C8C", flet.ControlState.DEFAULT: "#3978A8"},
                            ),
                        ),
                    ]),
                ])
                self._page.update()

            settings_cancel = newgame_cancel

            def credits_call(_):
                for main_button in main_column.controls:
                    main_button.disabled = True

                additional_column.controls.extend([
                    flet.Row([
                        flet.Container(width=10),
                        flet.Text("Settings:", weight=flet.FontWeight.W_600, size=30)
                    ]),
                    flet.Column([
                        flet.Row([
                            flet.Text("Leonid\nAbdrakhmanov", weight=flet.FontWeight.W_600, size=14, width=105),
                            flet.Container(width=4, height=50, bgcolor="#36618E"),
                            flet.Text("Application Interface\n...", weight=flet.FontWeight.W_600, size=14, color="#36618E"),
                        ]),
                        flet.Row([
                            flet.Text("Miras\nNuraly", weight=flet.FontWeight.W_600, size=14, width=105),
                            flet.Container(width=4, height=50, bgcolor="#36618E"),
                            flet.Text("Chess Engine", weight=flet.FontWeight.W_600, size=14, color="#36618E"),
                        ]),
                    ]),
                    flet.Row([
                        start_game_button := flet.Button(
                            disabled=True,
                            content=flet.Text("Start Game"),
                            on_click=lambda _: print("START GAME"),
                            width=100,
                            style=flet.ButtonStyle(
                                shape=flet.RoundedRectangleBorder(radius=9),
                                color="#FFFFFF",
                                bgcolor={flet.ControlState.DISABLED: "#8C8C8C", flet.ControlState.DEFAULT: "#3978A8"},
                            ),
                        ),
                        flet.Button(
                            content=flet.Text("Cancel"),
                            on_click=settings_cancel,
                            width=70,
                            style=flet.ButtonStyle(shape=flet.RoundedRectangleBorder(radius=9)),
                        ),
                    ]),
                ])
                self._page.update()

            def credits_cancel(_):
                return newgame_cancel(_)

            def quit_call(_):
                quit_dialog = flet.AlertDialog(
                    modal=True,
                    content=flet.Text("Are you sure you want to quit?"),
                    title=flet.Text("Confirm Exit"),
                    on_dismiss=lambda _: self._page.close(quit_dialog),
                    actions=[
                        flet.TextButton("Yes", on_click=lambda _: self._page.window.close()),
                        flet.TextButton("No", on_click=lambda _: self._page.close(quit_dialog)),
                    ]
                )
                self._page.open(quit_dialog)

            menu = flet.Row(controls=[
                spacing_column_0 := flet.Column(controls=[flet.Container(width=100)]),
                main_column := flet.Column(controls=[
                    main_newgame_button := flet.Button(
                        content=flet.Text("New Game", text_align=flet.TextAlign.CENTER, size=30), height=60, width=250,
                        on_click=newgame_call,
                        style=flet.ButtonStyle(shape=flet.RoundedRectangleBorder(radius=10)),
                    ),
                    main_loadgame_button := flet.Button(
                        content=flet.Text("Load Game", text_align=flet.TextAlign.CENTER, size=30), height=60, width=250,
                        on_click=loadgame_call,
                        style=flet.ButtonStyle(shape=flet.RoundedRectangleBorder(radius=10)),
                    ),
                    main_settings_button := flet.Button(
                        content=flet.Text("Settings", text_align=flet.TextAlign.CENTER, size=30), height=60, width=250,
                        on_click=settings_call,
                        style=flet.ButtonStyle(shape=flet.RoundedRectangleBorder(radius=10)),
                    ),
                    main_credits_button := flet.Button(
                        content=flet.Text("Credits", text_align=flet.TextAlign.CENTER, size=30), height=60, width=250,
                        on_click=credits_call,
                        style=flet.ButtonStyle(shape=flet.RoundedRectangleBorder(radius=10)),
                    ),
                    main_quit_button := flet.Button(
                        content=flet.Text("Quit", text_align=flet.TextAlign.CENTER, size=30), height=60, width=250,
                        on_click=quit_call,
                        style=flet.ButtonStyle(shape=flet.RoundedRectangleBorder(radius=10)),
                    ),
                ]),
                spacing_column_0 := flet.Column(controls=[flet.Container(width=100)]),
                additional_column := flet.Column(),
            ])
            self._page.controls.append(title_label)
            self._page.controls.append(menu)

        def _show_scene_mainmenu(self):
            self._page.clean()
            self._add_scene_mainmenu()
            self._page.update()

        def _add_scene_chess(self):
            self._application._input_listener.start()
            Cell = Application.Scene._Cell
            Cell.set_scene_self(self)
            Piece = Application.Scene._Piece
            BoardStack = Application.Scene._BoardStack
            BoardStack.set_scene_self(self)

            self.shift_pressed = False

            def register_shift():
                self.shift_pressed = self._application._input_listener.shift_pressed

            def get_active_piece() -> Piece | None:
                for piece in self.pieces:
                    piece: Piece
                    if piece.is_empty: continue
                    if piece.is_active():
                        return piece
                return None

            def get_selected_piece_all() -> list[Piece]:
                all_pieces: list[Piece] = []
                for piece in self.pieces:
                    if piece.selected:
                        all_pieces.append(piece)
                return all_pieces

            def get_piece_by_pos(piece_position: tuple[int, int]) -> Piece | None:
                for piece in self.pieces:
                    if tuple(transform_to_engine(*piece.ij)) == tuple(piece_position):
                        return piece
                return None

            def get_deselected_piece() -> Piece:
                for piece in self.pieces:
                    if piece.is_deselected():
                        return piece
                return None

            self.get_active_piece = get_active_piece

            def active_piece_set(event: flet.ControlEvent):
                piece_current: Piece = event.control
                # print("WHITE" if piece_current.board_piece.color == 2 else "BLACK")
                register_shift()
                if self.shift_pressed:
                    self.board_stack.free_layer_save()
                    self.board_stack.new_free_layer(piece_current.ij)
                    print(self.board_stack._free_layer)
                    piece_current.content_feedback.opacity = 0
                    piece_current.content_when_dragging.opacity = 1
                    piece_current.update()
                    return
                if piece_current.is_empty: return
                if piece_current.board_piece.color != self.current_color:
                    piece_current.content_feedback.opacity = 0
                    piece_current.content_when_dragging.opacity = 1
                    piece_current.update()
                    return
                piece_current.content_feedback.opacity = 1
                self.board_stack.clear()
                # piece_current.content_feedback.opacity = 0.5

                piece_current_is_active = piece_current.is_active()
                piece_current_selected = piece_current.selected
                for piece in self.pieces:
                    piece: Piece
                    piece.active = 0
                    # PIECE_CURRENT SET 0
                    piece.selected = False
                    piece.on_drag_start = active_piece_set
                piece_current.selected = piece_current_selected
                if piece_current_is_active:
                    piece_current.active = 4
                    # PIECE_CURRENT SET 4
                else:

                    piece_current.active = 1
                    # PIECE_CURRENT SET 1
                    print(*[
                        transform_from_engine(*t) for t in
                        piece_current.board_piece.get_legal_moves(
                            self._application._chess_engine, *transform_to_engine(*piece_current.ij)
                        )
                    ], sep="\n  ")
                    for xy in [
                        transform_from_engine(*t) for t in
                        piece_current.board_piece.get_legal_moves(
                            self._application._chess_engine, *transform_to_engine(*piece_current.ij)
                        )
                    ]:
                        Cell.get_cell(*xy).active = True
                    show_possible_moves(transform_to_engine(*get_active_piece().ij))

            def active_piece_drop(event: flet.ControlEvent):
                piece_current = event.control
                if self.shift_pressed:
                    return
                if piece_current.is_empty: return
                if piece_current.is_active():
                    piece_current.active = 2
                    # PIECE_CURRENT SET 2

            def deselect_piece(deselected_piece: Piece):
                hide_hint_moves()
                deselected_piece.selected = False
                deselected_piece.on_drag_start = active_piece_set

            def deselect_piece_all():
                for piece in self.pieces:
                    piece.selected = False

            def show_possible_moves(piece_position: tuple[int, int]):
                active_piece: Piece = get_piece_by_pos(piece_position)
                if self.shift_pressed:
                    return
                if active_piece.is_empty: return
                active_piece.on_drag_start = lambda event: hide_hint_moves(event.control)
                hide_hint_moves()
                active_piece.selected = True
                for move in active_piece.board_piece.get_legal_moves(self._application._chess_engine, *piece_position):
                    move_transformed = transform_from_engine(*move)
                    cell_possiblemove: Cell = Cell.get_cell(*move_transformed)
                    cell_possiblemove.set_bgc(cell_possiblemove.get_bgc_possible_moves())
                    cell_possiblemove.content.on_click = lambda event: piece_accept(Cell.get_cell(*event.control.id))
                    cell_possiblemove.save_color()
                    cell_possiblemove.update()

            def show_premove(piece_position: tuple[int, int]):
                for move in self.get_active_piece().board_piece.get_possible_moves(self._application._chess_engine, *piece_position):
                    move_transformed = transform_from_engine(*move)
                    cell_possiblemove: Cell = Cell.get_cell(*move_transformed)
                    cell_possiblemove.set_bgc(cell_possiblemove.get_bgc_premove())
                    cell_possiblemove.save_color()
                    cell_possiblemove.update()

            def hide_hint_moves(piece: Piece | None = None):
                if self.shift_pressed:
                    return
                if piece is not None:
                    if piece.is_empty: return
                    print(piece.active, piece.selected, piece.on_drag_start)
                    piece.active = 0
                    # PIECE_CURRENT SET 0
                    piece.on_drag_start = active_piece_set
                    piece.selected = False

                for i in range(8):
                    for j in range(8):
                        cell = Cell.get_cell(i, j)
                        cell.set_bgc(cell.get_bgc_inactive())
                        cell.save_color()
                        cell.content.on_click = None
                        # cell.update()

                self._page.update()

            def transform_to_engine(x, y):
                return (y, 7 - x)

            def transform_from_engine(x, y):
                return (7-y, x)

            def change_color():
                self.current_color = testfilechess.Color.invert(self.current_color)
                for piece in self.pieces:
                    piece: Piece
                    if piece.is_empty: continue
                    if piece.board_piece.color == self.current_color:
                        piece.content_feedback.opacity = 1
                        piece.content_when_dragging.opacity = Application.Scene.CONTENT_WHEN_DRAGGING_OPACITY
                    else:
                        piece.content_feedback.opacity = 0
                        piece.content_when_dragging.opacity = 1
                self._page.update()

            def piece_update(x, y, piece=None):
                if piece is not None:
                    Cell.get_cell(x, y).content.content = piece
                self._page.update()

            # setting the labels for letters and numbers
            if True:
                # self._add_menu_bar()

                board_border_width = 4
                self.cell_size = 46
                board_numbering_size = [30, 30]
                letters = "ABCDEFGH"

                board_letter_labels = flet.Row([flet.Container(width=board_numbering_size[0] + board_border_width)] + [
                    flet.Container(flet.Text(f"{letters[i]}",
                                             style=flet.TextStyle(weight=flet.FontWeight.W_700),
                                             text_align=flet.TextAlign.CENTER), width=self.cell_size)
                    for i in range(8)], height=board_numbering_size[1], spacing=0)
                board_letter_labels_empty = copy.copy(board_letter_labels)
                board_letter_labels_empty.controls = None

                board_number_labels = flet.Column([
                    flet.Container(flet.Text(f"{i+1}",
                                             style=flet.TextStyle(weight=flet.FontWeight.W_700),
                                             text_align=flet.TextAlign.CENTER),
                                   alignment=flet.Alignment(y=flet.MainAxisAlignment.CENTER, x=flet.MainAxisAlignment.CENTER), height=self.cell_size)
                    for i in range(8)[::-1]], width=board_numbering_size[0], spacing=0)
                board_number_labels_empty = copy.copy(board_number_labels)
                board_number_labels_empty.controls = None

            def piece_accept(cell: Cell):
                if self.shift_pressed:
                    self.board_stack.free_layer_save()
                    self.shift_pressed = False
                    return
                active_piece = get_active_piece()
                if active_piece is None: return
                if not active_piece.is_active() or not cell.active: return

                piece_prev = get_piece_by_pos(transform_to_engine(cell.i, cell.j))
                self.pieces.remove(piece_prev)
                captured, castling = self._application._chess_engine.move_chessman(
                    transform_to_engine(*active_piece.ij),
                    transform_to_engine(cell.i, cell.j)
                )
                captured = transform_from_engine(*captured)
                print("[]", captured)
                print("[]", cell.i, cell.j)
                cell_captured = Cell.get_cell(*captured)
                cell_captured.set_bgc(cell.get_bgc_inactive())
                new_empty_piece(*captured)
                cell_captured.update()

                cell.set_bgc(cell.get_bgc_inactive())
                new_empty_piece(*active_piece.ij)
                cell.update()
                active_piece.ij = [cell.i, cell.j]
                # if cell.id_accept == active_piece.id:
                piece_update(*active_piece.ij, active_piece)
                active_piece.active = 3
                # PIECE_CURRENT SET 3
                hide_hint_moves()
                active_piece.on_drag_start = active_piece_set
                change_color()
                for i in range(8):
                    for j in range(8):
                        Cell.get_cell(i, j).active = False

                if castling:
                    print()
                    rook: Piece = get_piece_by_pos((7 if captured[1] == 6 else 0, 7-captured[0]))
                    pos_new = (captured[0], 5 if captured[1] == 6 else 3)
                    Cell.get_cell(*pos_new).active = True
                    rook.active = 2
                    piece_accept(Cell.get_cell(*pos_new))
                    change_color()

            def piece_will_accept(event):
                cell: Cell = event.control
                if self.shift_pressed:
                    self.board_stack.free_layer_update((cell.i, cell.j))
                    return
                active_piece = get_active_piece()
                if active_piece is None: return
                if not active_piece.is_active() or not cell.active: return
                self.cell_mouse_over = cell
                print(f"{cell.active}")
                if active_piece is None:
                    return
                elif cell.active and active_piece.is_active():
                    cell.save_color()
                    cell.set_bgc(cell.get_bgc_active())
                    cell.update()

            def piece_leave(event):
                cell: Cell = event.control
                if self.shift_pressed:
                    return
                cell.set_bgc(cell.color_saved)
                cell.update()

            def create_cell(i, j: int) -> Cell:
                cell: Cell = Cell(
                    group=None,
                    on_accept=lambda event: piece_accept(event.control),
                    on_will_accept=piece_will_accept,
                    on_leave=piece_leave,
                    on_move=lambda _:None,
                    content=flet.Container(
                        width=self.cell_size, height=self.cell_size,
                        alignment=flet.Alignment(x=flet.MainAxisAlignment.CENTER, y=flet.MainAxisAlignment.CENTER),
                    )
                )
                cell.i = i
                cell.j = j
                cell.active = False
                cell.content.id = (i, j)
                cell.id_accept = None
                cell.set_bgc(cell.get_bgc_inactive())
                cell.save_color()
                return cell

            # adding layout elements to the page
            if True:
                self.board_cells = flet.Column([
                    flet.Row([
                        create_cell(i, j)
                        for j in range(8)], spacing=0)
                    for i in range(8)[::-1]], spacing=0)

                self.board_stack = Application.Scene._BoardStack([self.board_cells])

                self._page.controls.append(flet.Text("Black"))
                self._page.controls.append(
                    flet.Row([
                        flet.Container(width=30),
                        flet.Column([board_letter_labels
                                     if self._application._settings.board_two_sided_indexing else
                                     board_letter_labels_empty] + [
                            flet.Row([board_number_labels] + [
                                flet.Container(
                                    self.board_stack,
                                    border=flet.border.all(board_border_width, "#36618E"),
                                ),
                            ] + [board_number_labels
                                 if self._application._settings.board_two_sided_indexing else
                                 board_number_labels_empty], spacing=0),
                        ] + [board_letter_labels],
                                    spacing=0),
                    ])
                )

            # spawn pieces
            if True:
                def new_empty_piece(x, y):
                    image_src = "./resources/" + "Empty.png"
                    self.pieces.append(Piece(
                        content=flet.Image(src=image_src, width=self.cell_size - 2,
                                           height=self.cell_size - 2, opacity=1),
                        content_when_dragging=flet.Image(src=image_src, width=self.cell_size - 2,
                                                         height=self.cell_size - 2, opacity=1),
                        content_feedback=flet.Image(src=image_src, width=self.cell_size - 2, height=self.cell_size - 2,
                                                    opacity=1),
                        on_drag_start=active_piece_set,
                        on_drag_complete=active_piece_drop,
                        max_simultaneous_drags=2,
                    ))
                    self.pieces[-1].is_empty = True
                    self.pieces[-1].ij = (x, y)
                    self.pieces[-1].id = self.pieces[-2].id + 1 if len(self.pieces) > 1 else 0
                    piece_update(x, y, self.pieces[-1])

                def new_piece(x, y, board_piece):
                    image_src = (
                        "./resources/" +
                        ("White" if board_piece.color == testfilechess.Color.WHITE else "Black") +
                        ("Pawn" if board_piece.CODE == testfilechess.ChessmanPawn.CODE else
                         "Knight" if board_piece.CODE == testfilechess.ChessmanKnight.CODE else
                         "Bishop" if board_piece.CODE == testfilechess.ChessmanBishop.CODE else
                         "Rook" if board_piece.CODE == testfilechess.ChessmanRook.CODE else
                         "Queen" if board_piece.CODE == testfilechess.ChessmanQueen.CODE else
                         "King" if board_piece.CODE == testfilechess.ChessmanKing.CODE else "") +
                        ".png"
                    )
                    self.pieces.append(Piece(
                        content=flet.Image(src=image_src, width=self.cell_size - 2, height=self.cell_size - 2, opacity=1),
                        content_when_dragging=flet.Image(src=image_src, width=self.cell_size - 2,
                                                         height=self.cell_size - 2, opacity=0.5),
                        content_feedback=flet.Image(src=image_src, width=self.cell_size - 2, height=self.cell_size - 2,
                                                    opacity=1),
                        on_drag_start=active_piece_set,
                        on_drag_complete=active_piece_drop,
                        max_simultaneous_drags=2,
                    ))
                    self.pieces[-1].content_feedback_saved = self.pieces[-1].content_feedback
                    self.pieces[-1].is_empty = False
                    self.pieces[-1].group = None
                    self.pieces[-1].active = 0
                    self.pieces[-1].selected = False
                    self.pieces[-1].ij = (x, y)
                    self.pieces[-1].id = self.pieces[-2].id + 1 if len(self.pieces) > 1 else 0
                    self.pieces[-1].board_piece = board_piece
                    piece_update(x, y, self.pieces[-1])

                self.pieces = list()
                for x in range(8):
                    for y in range(8):
                        board_piece = self._application._chess_engine.get_chessman(*transform_to_engine(x, y))
                        if board_piece.CODE != testfilechess.EmptyCell.CODE:
                            new_piece(x, y, board_piece)
                        else:
                            new_empty_piece(x, y)
                self.current_color = testfilechess.Color.WHITE

        def _show_scene_chess(self):
            self._page.clean()
            self._add_scene_chess()
            self._page.update()

    class KeyboardListener:
        _application: Application
        shift_pressed: bool
        shift_counts: bool
        _listener: pynput.keyboard.Listener

        def __init__(self, application: Application):
            def on_press(key: pynput.keyboard.Key):
                if key is pynput.keyboard.Key.shift:
                    self.shift_pressed = True
                    self._register_press(key)

            def on_release(key: pynput.keyboard.Key):
                if key is pynput.keyboard.Key.shift:
                    self.shift_pressed = False
                    self._register_release(key)

            self._application = application
            self.shift_pressed = False
            self._listener = pynput.keyboard.Listener(on_press=on_press, on_release=on_release)

        def start(self):
            self._listener.start()

        def stop(self):
            self._listener.stop()

        def _register_press(self, key: pynput.keyboard.Key):
            if key is pynput.keyboard.Key.shift:
                if self._application._scene.get_active_piece() is not None: return
                # print("REGISTER PRESS")
                self.shift_counts = True
                for piece in self._application._scene.pieces:
                    piece.content_feedback_saved_opacity = 0
                # self._application._scene.board_stack.free_layer_show()

        def _register_release(self, key: pynput.keyboard.Key):
            if key is pynput.keyboard.Key.shift:
                if self._application._scene.get_active_piece() is not None: return
                self.shift_counts = False
                # print("REGISTER RELEASE")
                for piece in self._application._scene.pieces:
                    piece.content_feedback_saved_opacity = 1
                # self._application._scene.board_stack.free_layer_hide()

        def __del__(self):
            self._listener.stop()

    _chess_engine: testfilechess.Chessboard
    _players: list[bool, bool]
    _pc_difficulty: int
    _pc_difficulty_max: int = 3
    _settings: Application.Settings
    _input_listener: Application.KeyboardListener
    _scene: Application.Scene

    def __init__(self):
        self._chess_engine = testfilechess.Chessboard()
        self._chess_engine.fill()
        self._players = [True, True]
        self._pc_difficulty = 1
        self._settings = Application.Settings("settings.json")
        self._input_listener = Application.KeyboardListener(self)
        self._scene = Application.Scene(self)

    def run(self):
        self._scene.run()

    def __str__(self):
        return ("Application object {\n" +
                f"    ChessEngine: {ChessEngine},\n" +
                "}")

    def change_player(self, player_id: int) -> bool:  # returns True if the operation has changed two parameters, else returns False
        if player_id not in (0, 1):
            raise ValueError(f"Can't change the player with id {player_id}. The number is supposed to be either 0 or 1.")
        # ↓ Checks if the changing player [first] is set to player. If not, the following situation is going to be
        if not self._players[player_id]:
            self._players[player_id] = True
            return False
        # [we know the first player is set to pc]
        self._players[player_id] = False
        # ↓ If the other player is also PC, change him to player in order not to have two computers.
        if not self._players[1 - player_id]:
            self._players[1 - player_id] = True
            return True  # this means we change both players, then we return True.
        return False
