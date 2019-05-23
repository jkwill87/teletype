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

__all__ = ["Select", "SelectMany", "ProgressBar"]


class Component:
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


class Select(Component):
    _col_offset: int
    _line: int
    can_quit: bool
    can_skip: bool
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
        self._col_offset = 2
        # Set skip text
        self.can_skip = True if config.get("skip") else False
        if self.can_skip:
            if self.ascii_mode:
                s = "[s]kip"
            else:
                s = io.style_format("s", "dark underline")
                s += io.style_format("kip", "dark")
            self.choices.append(s)
        # Set quit text
        self.can_quit = True if config.get("quit") else False
        if self.can_quit:
            if self.ascii_mode:
                s = "[q]uit"
            else:
                s = io.style_format("q", "dark underline")
                s += io.style_format("uit", "dark")
            self.choices.append(s)

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

    def prompt(self) -> Optional[str]:
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
        while True:
            key = io.get_key()
            if key in {"up", "k"}:
                self._move_line(-1)
            elif key in {"down", "j"}:
                self._move_line(1)
            elif key in {"ctrl-c", "ctrl-d", "ctrl-z"} | codes.ESCAPE_SEQUENCES:
                io.move_cursor(0, len(self.choices) - self._line)
                io.show_cursor()
                raise TeletypeQuitException
            elif key == "s" and self.can_skip:
                distance = len(self.choices) - self._line - 1
                if self.can_quit:
                    distance -= 1
                if not self._move_line(distance):
                    break
            elif key == "q" and self.can_quit:
                distance = len(self.choices) - self._line - 1
                if not self._move_line(distance):
                    break
            elif key in ("lf", "nl"):
                break
        if self.erase_screen:
            io.erase_screen()
        else:
            io.move_cursor(rows=len(self.choices) - self._line)
        io.show_cursor()
        if self.can_quit and self.selected in ("quit", "[q]uit"):
            raise TeletypeQuitException
        elif self.can_skip and self.selected in ("skip", "[s]kip"):
            raise TeletypeSkipException
        return self.selected

    @property
    def selected(self) -> str:
        choice = self.choices[self._line % len(self.choices)]
        if isinstance(choice, str):
            choice = io.strip_format(choice)
        return choice


class SelectMany(Select):
    _selected_lines: Set[int]

    def __init__(self, choices: Any, **config: Any) -> None:
        config["quit"] = False
        config["skip"] = False
        super().__init__(choices, **config)
        self._selected_lines = set()
        self._col_offset = 1

    def _select_line(self) -> None:
        self._selected_lines ^= {self._line}
        io.move_cursor(cols=1)
        if self._line in self._selected_lines:
            glyph = self._get_glyph("selected")
        else:
            glyph = self._get_glyph("unselected")
        print(glyph, end="")
        io.move_cursor(cols=-2)

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
        while True:
            key = io.get_key()
            if key in {"up", "k"}:
                self._move_line(-1)
            elif key in {"down", "j"}:
                self._move_line(1)
            elif key in {"ctrl-c", "ctrl-d", "ctrl-z"} | codes.ESCAPE_SEQUENCES:
                io.move_cursor(0, len(self.choices) - self._line)
                io.show_cursor()
                raise TeletypeQuitException
            elif key == "space":
                self._select_line()
            elif key in ("lf", "nl"):
                break
        if self.erase_screen:
            io.erase_screen()
        else:
            io.move_cursor(rows=len(self.choices) - self._line)
        io.show_cursor()
        return self.selected

    @property
    def selected(self) -> Tuple[Any, ...]:
        return tuple(
            self.choices[line % len(self.choices)]
            for line in self._selected_lines
        )


class ProgressBar(Component):
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
