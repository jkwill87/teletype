from __future__ import print_function

from copy import deepcopy
from os import get_terminal_size
from typing import (
    Any,
    Collection,
    Dict,
    Iterable,
    List,
    Optional,
    Set,
    Tuple,
    Union,
)

from teletype import codes, io
from teletype.exceptions import TeletypeQuitException, TeletypeSkipException

__all__ = ["SelectOne", "SelectMany", "ProgressBar"]


class _Component:
    _ascii_mode: bool
    _backups: Tuple
    display_chars: Dict[str, Dict[str, str]]
    erase_screen: bool
    header: str
    style_primary: Union[Collection[str], str, None]
    style_secondary: Union[Collection[str], str, None]

    def __init__(self, **config: Any) -> None:
        self._backups = ()
        self.ascii_mode = config.get("ascii_mode", False)
        self.display_chars = config.get(
            "display_chars", deepcopy(codes.DEFAULT_CHARS)
        )
        self.erase_screen = config.get("erase_screen", False)
        self.header = config.get("header", "").strip().rstrip(":")
        self.style_primary = config.get("style_primary", "green")
        self.style_secondary = config.get("style_secondary", "dark green")

    def _get_char_category(self, key: str) -> str:
        for category, d in self.display_chars.items():
            if key in d.keys():
                return category
        raise KeyError

    def _get_glyph(self, key: str) -> str:
        category = self._get_char_category(key)
        if not category:
            raise KeyError
        glyph = self.display_chars[category][key]
        if category == "primary":
            glyph = io.style_format(glyph, self.style_primary)
        elif category == "secondary":
            glyph = io.style_format(glyph, self.style_secondary)
        return glyph

    @property
    def ascii_mode(self) -> bool:
        return getattr(self, "_ascii_mode", False)

    @ascii_mode.setter
    def ascii_mode(self, enabled: bool):
        """ Disables color and switches to an ASCII character set if True.
        """
        enabled = True if enabled else False
        if not (enabled or self._backups) or (enabled and self.ascii_mode):
            return
        if enabled:
            self._backups = (
                self.display_chars.copy(),
                self.style_primary,
                self.style_secondary,
            )
            self.display_chars = deepcopy(codes.ASCII_CHARS)
            self.style_primary = None
            self.style_secondary = None
        else:
            self.display_chars, self.style_primary, self.style_secondary = (
                self._backups
            )
        self._ascii_mode = enabled

    def char_set(self, key, value):
        """ Updates charters used to render components.
        """
        category = self._get_char_category(key)
        if not category:
            raise KeyError
        self.display_chars[category][key] = value


class _Select(_Component):
    _selected_lines: Set[int]
    _col_offset: int
    _line: int
    choices: List[Any]

    def __init__(self, choices: Any, **config: Any):
        super().__init__(**config)
        unique_choices: Set[Any] = set()
        self.choices = []
        for choice in choices:
            if choice not in unique_choices:
                unique_choices.add(choice)
                self.choices.append(choice)
        self._line = 0
        self._selected_lines = set()
        self._col_offset = 1

    def _add_skip_choice(self) -> List[Any]:
        if self.ascii_mode:
            s = "[s]kip"
        else:
            s = io.style_format("s", "dark underline")
            s += io.style_format("kip", "dark")
        return self.choices + [s]

    def _add_quit_choice(self):
        if self.ascii_mode:
            s = "[q]uit"
        else:
            s = io.style_format("q", "dark underline")
            s += io.style_format("uit", "dark")
        return self.choices + [s]

    def _select_line(self) -> None:
        self._selected_lines ^= {self._line}
        io.move_cursor(cols=1)
        if self._line in self._selected_lines:
            glyph = self._get_glyph("selected")
        else:
            glyph = self._get_glyph("unselected")
        print(glyph, end="")
        io.move_cursor(cols=-2)

    def _move_line(self, distance: int) -> int:
        # col_offset logic is used to properly clear whitespace before choices
        g_cursor = self._get_glyph("arrow")
        offset = (self._line + distance) % len(self.choices) - self._line
        if offset == 0:
            return 0
        self._line += offset
        print(" " * self._col_offset, end="")
        io.move_cursor(rows=offset, cols=-self._col_offset)
        print("%s%s" % (" " * (self._col_offset - 1), g_cursor), end="")
        io.move_cursor(cols=-self._col_offset)
        return offset

    def _capture_keypress(
        self,
        accept_s=False,
        accept_q=False,
        accept_space=False,
        accept_escape=False,
    ):
        while True:
            key = io.get_key()
            # navigation key pressed
            if key in {"up", "k"}:
                self._move_line(-1)
            elif key in {"down", "j"}:
                self._move_line(1)
            # escape sequences pressed
            elif (
                accept_escape
                and key
                in {"ctrl-c", "ctrl-d", "ctrl-z"} | codes.ESCAPE_SEQUENCES
            ):
                io.move_cursor(0, len(self.choices) - self._line)
                io.show_cursor()
                raise TeletypeQuitException
            # enter pressed
            elif key in ("lf", "nl"):
                break
            # space pressed
            elif accept_space and key == "space":
                self._select_line()
            # skip selected
            elif accept_s and key == "s":
                distance = len(self.choices) - self._line - 1
                if accept_q:
                    distance -= 1
                if not self._move_line(distance):
                    break
            # quit selected
            elif accept_q and key == "q":
                distance = len(self.choices) - self._line - 1
                if not self._move_line(distance):
                    break

    @property
    def highlighted(self) -> str:
        choice = self.choices[self._line % len(self.choices)]
        if isinstance(choice, str):
            choice = io.strip_format(choice)
        return choice

    @property
    def selected(self) -> Tuple[Any, ...]:
        return tuple(
            self.choices[line % len(self.choices)]
            for line in self._selected_lines
        )


class SelectOne(_Select):
    def __init__(self, choices: Any, **config: Any):
        super().__init__(choices, **config)
        self._col_offset = 2

    def prompt(
        self, can_skip: bool = False, can_quit: bool = False
    ) -> Optional[str]:
        self._line = 0
        g_cursor = self._get_glyph("arrow")
        if not self.choices:
            return None
        io.hide_cursor()
        if self.erase_screen:
            io.erase_screen()
        if self.header:
            style = None if self.ascii_mode else "bold"
            io.style_print(self.header + ":", style=style)
        for i, choice in enumerate(self.choices):
            print(" %s %s" % (g_cursor if i == 0 else " ", choice))
        io.move_cursor(rows=-1 * i - 1)
        self._capture_keypress(
            accept_escape=True, accept_s=can_skip, accept_q=can_quit
        )
        if self.erase_screen:
            io.erase_screen()
        else:
            io.move_cursor(rows=len(self.choices) - self._line)
        io.show_cursor()
        if can_quit and self.selected in ("quit", "[q]uit"):
            raise TeletypeQuitException
        elif can_skip and self.selected in ("skip", "[s]kip"):
            raise TeletypeSkipException
        return self.highlighted


class SelectMany(_Select):
    _selected_lines: Set[int]

    def prompt(self) -> Tuple[Any, ...]:
        self._line = 0
        self._selected_lines = set()
        g_arrow = self._get_glyph("arrow")
        g_unselected = self._get_glyph("unselected")
        if not self.choices:
            return tuple()
        io.hide_cursor()
        if self.erase_screen:
            io.erase_screen()
        if self.header:
            style = None if self.ascii_mode else "bold"
            io.style_print(self.header + ":", style=style)
        for i, choice in enumerate(self.choices):
            print("%s%s %s " % (" " if i else g_arrow, g_unselected, choice))
        io.move_cursor(rows=-1 * i - 1)
        self._capture_keypress(accept_escape=True, accept_space=True)
        if self.erase_screen:
            io.erase_screen()
        else:
            io.move_cursor(rows=len(self.choices) - self._line)
        io.show_cursor()
        return self.selected


class ProgressBar(_Component):
    width: int

    def __init__(self, **config):
        super().__init__(**config)
        try:
            self.width = config.get("width", get_terminal_size().columns)
        except OSError:
            self.width = 80

    def process(self, iterable: Iterable, steps: int) -> None:
        io.hide_cursor()
        self.update(0, steps)
        skip_count = max(steps // 1000, 1)
        for step, _ in enumerate(iterable, 1):
            if step % skip_count == 0 or step == steps:
                self.update(step, steps)
        io.show_cursor()
        print()

    def update(self, step: int, steps: int) -> None:
        g_block = self._get_glyph("block")
        g_l_edge = self._get_glyph("left-edge")
        g_r_edge = self._get_glyph("right-edge")
        prefix = ""
        if self.header:
            prefix += "%s: " % io.style_format(self.header, "bold")
        format_specifier = "%%0%dd" % len(str(steps))
        prefix += "%s/%d%s" % (format_specifier % step, steps, g_l_edge)
        suffix = g_r_edge + "%03d%%" % (step / steps * 100)
        units_total = max(self.width - len(io.strip_format(prefix + suffix)), 5)
        units = units_total * step // steps
        line = prefix + units * g_block + (units_total - units) * " " + suffix
        print("\r%s" % line, end="")
