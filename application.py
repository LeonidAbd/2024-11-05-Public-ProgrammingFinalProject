from __future__ import annotations

import copy
import json
import flet
import flet.canvas
from typing import Callable
import pynput

from chess_engine import *


class Application:
    class Settings:
        board_two_sided_indexing: bool

        def __init__(self, filename):
            settings_json = json.load(open(filename, "r"))
            for key, value in settings_json.items():
                self.__setattr__(key, value["value"])

    class Scene:
        class _Cell(flet.DragTarget):
            i: int; j: int; active: bool; color_saved: str; content: flet.Container
            _scene_self: Application.Scene | None = None
            
            @staticmethod
            def set_scene_self(scene: Application.Scene):
                Application.Scene._Cell._scene_self = scene

            def get_color(self):
                return "#B0B0B0" if (self.i + self.j) % 2 == 0 else "#E0E0E0"

            def get_color_active(self):
                return "#84B09A" if (self.i + self.j) % 2 == 0 else "#A6DEC2"

            def get_color_history(self):
                return "#93B084" if (self.i + self.j) % 2 == 0 else "#B9DEA6"

            def save_color(self):
                self.color_saved = self.content.bgcolor

            @staticmethod
            def get_cell(i, j) -> Application.Scene._Cell:
                return Application.Scene._Cell._scene_self.board_cells.controls[7 - i].controls[j]

        class _Piece(flet.Draggable):
            content_feedback_saved: flet.Image; ij: tuple[int, int]; id: int; is_active: int

        class _BoardStack(flet.Stack):
            _scene: Application.Scene | None

            @staticmethod
            def set_scene_self(scene: Application.Scene):
                Application.Scene._BoardStack._scene_self = scene

            class Layer(flet.canvas.Canvas):
                ij1: tuple[int, int]
                ij2: tuple[int, int] | None

                def line_update(self, ij2: tuple[int, int]):
                    self.ij2 = ij2
                    self.shapes = [flet.canvas.Line(
                        x1=Application.Scene._BoardStack._scene.cell_size * 80 +
                        Application.Scene._BoardStack._scene.cell_size / 2 * (1 + 2 * self.ij1[1]),
                        y1=Application.Scene._BoardStack._scene.cell_size * 80 +
                        Application.Scene._BoardStack._scene.cell_size / 2 * (15 - 2 * self.ij1[0]),
                        x2=Application.Scene._BoardStack._scene.cell_size * 80 +
                        Application.Scene._BoardStack._scene.cell_size / 2 * (1 + 2 * self.ij2[1]),
                        y2=Application.Scene._BoardStack._scene.cell_size * 80 +
                        Application.Scene._BoardStack._scene.cell_size / 2 * (15 - 2 * self.ij2[0]),
                        paint=flet.Paint(stroke_width=5, color="#36618E"),
                    )]

            _scene: Application.Scene | None
            _free_layer: Application.Scene._BoardStack.Layer | None = None
            _last_combination = 0

            def new_free_layer(self, ij1: tuple[int, int]):
                if self.free_layer_is_none():
                    return
                free_layer = Application.Scene._BoardStack.Layer(shapes=[
                ], top=0, left=0, opacity=0.5,
                    width=Application.Scene._BoardStack._scene.cell_size * 8, height=Application.Scene._BoardStack._scene.cell_size * 8,
                    offset=(-10, -10))
                free_layer.ij1 = ij1
                self.free_layer_set(free_layer)

            def free_layer_set(self, free_layer: Layer):
                if self.free_layer_is_none():
                    self.controls.append(None)
                self._free_layer = free_layer
                self.controls[-1] = free_layer
                self.update()

            def free_layer_is_none(self):
                if not hasattr(self, "_free_layer"):
                    self._free_layer = None
                return self._free_layer is None

            def free_layer_delete(self):
                if self.free_layer_is_none():
                    return
                self.controls.pop(-1)
                self._free_layer = None

            def free_layer_hide(self):
                if not self.free_layer_is_none():
                    self._free_layer.opacity = 0

            def free_layer_show(self):
                if not self.free_layer_is_none():
                    self._free_layer.opacity = 0.5

            def free_layer_is_hidden(self):
                if self.free_layer_is_none():
                    return None
                return self._free_layer.opacity <= 0

            def free_layer_save(self):
                self._free_layer.opacity = 1
                self._free_layer = None

        _application: Application
        _app_function: Callable[[flet.Page], None]
        _page: flet.Page
        pieces_current: list[Application.Scene._Piece]
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

                update_pc_difficulty = lambda: add_pc_difficulty(*[i for i in range(len(self._application._players)) if not self._application._players[i]])
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

            def get_active_piece() -> Piece:
                for cell in self.pieces_current:
                    if cell.active is 1:
                        return cell
                return None

            self.get_active_piece = get_active_piece

            def active_piece_set(event: flet.ControlEvent):
                print(event.control.ij)
                self.piece_current = event.control
                is_active = self.piece_current.is_active
                for piece in self.pieces_current:
                    piece: Piece
                    piece.is_active = 0
                if is_active == 1:
                    print("PIECECURRENT ERROR")
                else:
                    self.piece_current.is_active = 1
                    print("PIECECURRENT SET 1")

            def active_piece_drop(event: flet.ControlEvent):
                piece_current = event.control
                piece_current.is_active = 2
                print("PIECECURRENT SET 2")

            def piece_spawn():
                image_src = "./resources/WhiteRook.png"
                self.pieces_current = [Piece(
                    group=None,
                    content=flet.Image(src=image_src, width=cell_size - 2, height=cell_size - 2, opacity=1),
                    content_when_dragging=flet.Image(src=image_src, width=cell_size - 2, height=cell_size - 2, opacity=0.5),
                    content_feedback=flet.Image(src=image_src, width=cell_size - 2, height=cell_size - 2, opacity=1),
                    on_drag_start=active_piece_set,
                    on_drag_complete=active_piece_drop,
                )]
                for piece in self.pieces_current:
                    piece.is_active = 0
                self.pieces_current[0].content_feedback_saved = self.pieces_current[0].content_feedback
                self.pieces_current[0].ij = [1, 2]
                self.pieces_current[0].id = 1
                piece_update()

            def piece_update():
                Cell.get_cell(*self.pieces_current[0].ij).content.content = self.pieces_current[0]
                Cell.get_cell(1, 2).id_accept = 1
                Cell.get_cell(2, 2).id_accept = 1
                Cell.get_cell(3, 2).id_accept = 1

                self._page.update()

            # self._add_menu_bar()

            board_border_width = 4
            cell_size = 46
            board_numbering_size = [30, 30]
            letters = "ABCDEFGH"

            board_letter_labels = flet.Row([flet.Container(width=board_numbering_size[0] + board_border_width)] + [
                flet.Container(flet.Text(f"{letters[i]}",
                                         style=flet.TextStyle(weight=flet.FontWeight.W_700),
                                         text_align=flet.TextAlign.CENTER), width=cell_size)
                for i in range(8)], height=board_numbering_size[1], spacing=0)
            board_letter_labels_empty = copy.copy(board_letter_labels)
            board_letter_labels_empty.controls = None

            board_number_labels = flet.Column([
                flet.Container(flet.Text(f"{i+1}",
                                         style=flet.TextStyle(weight=flet.FontWeight.W_700),
                                         text_align=flet.TextAlign.CENTER),
                               alignment=flet.Alignment(y=flet.MainAxisAlignment.CENTER, x=flet.MainAxisAlignment.CENTER), height=cell_size)
                for i in range(8)[::-1]], width=board_numbering_size[0], spacing=0)
            board_number_labels_empty = copy.copy(board_number_labels)
            board_number_labels_empty.controls = None

            def piece_accept(event: flet.DragTargetAcceptEvent):
                event.control.content.bgcolor = event.control.get_color()
                event.control.content.border = flet.border.all(0, event.control.get_color())
                event.control.update()
                Cell.get_cell(*self.pieces_current[0].ij).content.content = None
                self.pieces_current[0].ij = [event.control.i, event.control.j]
                piece_update()

            def piece_will_accept(event):
                cell: Cell = event.control
                self.cell_mouse_over = cell
                if self._application._input_listener.shift_pressed:
                    print("SHIFT!")
                    self.board_stack.new_free_layer(self.pieces_current[0])
                    self._page.update()
                elif cell.id_accept == self.get_active_piece():
                    cell.save_color()
                    cell.content.bgcolor = cell.get_color_active()
                    cell.content.border = flet.border.all(0, cell.get_color_active())
                    # cell.content.border = flet.border.all(2, flet.Colors.BLACK45)
                    cell.update()

            def piece_leave(event):
                cell: Cell = event.control
                cell.content.bgcolor = cell.color_saved
                cell.content.border = flet.border.all(0, cell.color_saved)
                cell.update()

            def create_cell(i, j: int) -> Cell:
                cell: Cell = Cell(
                    group=None,
                    on_accept=piece_accept,
                    on_will_accept=piece_will_accept,
                    on_leave=piece_leave,
                    on_move=lambda _:None,
                    content=flet.Container(
                        width=cell_size, height=cell_size,
                        alignment=flet.Alignment(x=flet.MainAxisAlignment.CENTER, y=flet.MainAxisAlignment.CENTER),
                    )
                )
                cell.i = i
                cell.j = j
                cell.active = False
                cell.content.id = i * 8 + j
                cell.content.bgcolor = cell.get_color()
                cell.content.border = flet.border.all(0, cell.get_color())
                cell.save_color()
                return cell

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
                ]),
            )

            def piece_cell_fill_active(_):
                cell_og = Cell.get_cell(*self.pieces_current[0].ij)
                cell_og.content.bgcolor = cell_og.get_color_active()
                cell_og.content.border = flet.border.all(0, cell_og.get_color_active())

            piece_spawn()

        def _show_scene_chess(self):
            self._page.clean()
            self._add_scene_chess()
            self._page.update()

    class KeyboardListener:
        _application: Application
        shift_pressed: bool
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
                self._application._scene.pieces_current[0].content_feedback_saved.opacity = 0
                self._application._scene.board_stack.free_layer_show()

        def _register_release(self, key: pynput.keyboard.Key):
            if key is pynput.keyboard.Key.shift:
                self._application._scene.pieces_current[0].content_feedback_saved.opacity = 1
                self._application._scene.board_stack.free_layer_hide()

        def __del__(self):
            self._listener.stop()

    _chess_engine: ChessEngine
    _players: list[bool, bool]
    _pc_difficulty: int
    _pc_difficulty_max: int = 3
    _settings: Application.Settings
    _input_listener: Application.KeyboardListener
    _scene: Application.Scene

    def __init__(self):
        self._chess_engine = ChessEngine()
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

    def _get_piece(self, piece_type):
        self._chess_engine.get_pieces(piece_type)
