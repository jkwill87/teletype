# coding=utf-8

from __future__ import print_function

from copy import deepcopy

from teletype import codes
from teletype import io
from teletype.exceptions import (
    TeletypeQuitException,
    TeletypeSkipException,
    TeletypeException,
)

__all__ = ["Select", "SelectMany", "ProgressBar"]


class Component:
    def __init__(self, **config):
        self._backups = None
        self.erase_screen = config.get("erase_screen", False)
        self.display_chars = config.get(
            "display_chars", deepcopy(codes.DEFAULT_CHARS)
        )
        self.header = config.get("header", "").strip().rstrip(":")
        self.style_primary = config.get("style_primary", "green")
        self.style_secondary = config.get("style_secondary", "dark green")
        self.ascii_mode = config.get("ascii_mode", False)

    def _get_char_category(self, key):
        for category, d in self.display_chars.items():
            if key in d.keys():
                return category

    def _get_glyph(self, key):
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
    def ascii_mode(self):
        return getattr(self, "_ascii_mode", False)

    @ascii_mode.setter
    def ascii_mode(self, enabled):
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
    def __init__(self, choices, **config):
        Component.__init__(self, **config)
        unique_choices = set()
        self.choices = [
            choice
            for choice in choices
            if choice not in unique_choices
            and (unique_choices.add(choice) or True)
        ]
        self._line = 0
        self._col_offset = 2
        # Set skip text
        self._can_skip = config.get("skip")
        if self._can_skip:
            if self.ascii_mode:
                s = "[s]kip"
            else:
                s = io.style_format("s", "dark underline")
                s += io.style_format("kip", "dark")
            self.choices.append(s)

        # Set quit text
        self._can_quit = config.get("quit")
        if self._can_quit:
            if self.ascii_mode:
                s = "[q]uit"
            else:
                s = io.style_format("q", "dark underline")
                s += io.style_format("uit", "dark")
            self.choices.append(s)

    def _move_line(self, distance):
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

    def prompt(self):
        self._line = 0
        g_cursor = self._get_glyph("arrow")
        if not self.choices:
            return
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
            elif key == "s" and self._can_skip:
                distance = len(self.choices) - self._line - 1
                if self._can_quit:
                    distance -= 1
                if not self._move_line(distance):
                    break
            elif key == "q" and self._can_quit:
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
        if self._can_quit and self.selected in ("quit", "[q]uit"):
            raise TeletypeQuitException
        elif self._can_skip and self.selected in ("skip", "[s]kip"):
            raise TeletypeSkipException
        return self.selected

    @property
    def selected(self):
        choice = self.choices[self._line % len(self.choices)]
        if isinstance(choice, str):
            choice = io.strip_format(choice)
        return choice


class SelectMany(Select):
    def __init__(self, choices, **config):
        config["quit"] = False
        config["skip"] = False
        Select.__init__(self, choices, **config)
        self._selected_lines = set()
        self._col_offset = 1

    def _select_line(self):
        self._selected_lines ^= {self._line}
        io.move_cursor(cols=1)
        if self._line in self._selected_lines:
            glyph = self._get_glyph("selected")
        else:
            glyph = self._get_glyph("unselected")
        print(glyph, end="")
        io.move_cursor(cols=-2)

    def prompt(self):
        self._line = 0
        self._selected_lines = set()
        g_arrow = self._get_glyph("arrow")
        g_unselected = self._get_glyph("unselected")
        if not self.choices:
            return
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
    def selected(self):
        return [
            self.choices[line % len(self.choices)]
            for line in self._selected_lines
        ]


class ProgressBar(Component):
    def __init__(self, **config):
        Component.__init__(self, **config)
        width = config.get("width", False)
        if width:
            self.width = width
        else:
            try:
                # Python 3.3+ only
                self.width, _ = os.get_terminal_size()
            except:
                self.width = 80

    def process(self, iterable, iterations=None):
        try:
            steps = iterations or len(iterable)
        except AttributeError:
            raise TeletypeException("Unable to determine range")
        io.hide_cursor()
        self.update(0, steps)
        skip_count = max(steps // 1000, 1)
        for step, _ in enumerate(iterable, 1):
            if step % skip_count == 0 or step == steps:
                self.update(step, steps)
        io.show_cursor()
        print()

    def update(self, step, steps):
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
