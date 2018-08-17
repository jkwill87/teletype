# coding=utf-8

from __future__ import print_function

from teletype.codes import escape_sequences
from teletype.exceptions import (
    TeletypeQuitException,
    TeletypeSkipException,
    TeletypeException,
)
from teletype.io import (
    erase_lines,
    erase_screen,
    get_key,
    move_cursor,
    show_cursor,
    strip_format,
    style_format,
    style_print,
)

_chars = {
    "cursor": style_format(u"❯", "magenta"),
    "filled": style_format(u"⦿", "green"),
    "unfilled": u"○",
}


class SelectOne:
    def __init__(self, choices, header="", **options):
        self._line = 0
        unique_choices = set()
        self.choices = [
            choice
            for choice in choices
            if choice not in unique_choices
            and (unique_choices.add(choice) or True)
        ]
        self.header = header
        self.erase_screen = options.get("erase_screen") is True
        if options.get("show_skip") is True:
            self.show_skip = True
            self.choices.append(style_format("[SKIP]", "dark"))
        else:
            self.show_skip = False
        if options.get("show_quit") is True:
            self.show_quit = True
            self.choices.append(style_format("[QUIT]", "dark"))
        else:
            self.show_quit = False

    def prompt(self):
        if not self.choices:
            return
        show_cursor(False)
        if self.erase_screen:
            erase_screen()
        if self.header:
            style_print(self.header, style="bold")
        for i, choice in enumerate(self.choices):
            print(" %s %s" % (_chars["cursor"] if i == 0 else " ", choice))
        move_cursor(rows=-1 * i - 1)
        while True:
            key = get_key()
            if key in {"up", "k"}:
                self._move_line(-1)
            elif key in {"down", "j"}:
                self._move_line(1)
            elif key in {"ctrl-c", "ctrl-d", "ctrl-z"} | escape_sequences:
                show_cursor(True)
                raise TeletypeQuitException
            elif key == "lf":
                break
        if self.erase_screen:
            erase_screen()
        else:
            move_cursor(rows=len(self.choices) - self._line + 1)
        show_cursor(True)
        if self.show_quit and self.selected == "[QUIT]":
            raise TeletypeQuitException
        elif self.show_skip and self.selected == "[SKIP]":
            raise TeletypeSkipException
        return self.selected

    def _move_line(self, distance):
        offset = (self._line + distance) % len(self.choices) - self._line
        if offset == 0:
            return
        self._line += offset
        print("  ", end="")
        move_cursor(rows=offset, cols=-2)
        print(" %s" % _chars["cursor"], end="")
        move_cursor(cols=-2)

    @property
    def selected(self):
        choice = self.choices[self._line % len(self.choices)]
        if isinstance(choice, str):
            choice = strip_format(choice)
        return choice


class SelectMany:
    def __init__(self, choices, header="", **options):
        self._line = 0
        self._selected_lines = set()
        unique_choices = set()
        self.choices = [
            choice
            for choice in choices
            if choice not in unique_choices
            and (unique_choices.add(choice) or True)
        ]
        self.header = header
        self.erase_screen = options.get("erase_screen") is True

    def prompt(self):
        if not self.choices:
            return
        show_cursor(False)
        if self.erase_screen:
            erase_screen()
        if self.header:
            style_print(self.header, style="bold")
        for i, choice in enumerate(self.choices):
            print(
                "%s%s %s "
                % (" " if i else _chars["cursor"], _chars["unfilled"], choice)
            )
        move_cursor(rows=-1 * i - 1)
        while True:
            key = get_key()
            if key in {"up", "k"}:
                self._move_line(-1)
            elif key in {"down", "j"}:
                self._move_line(1)
            elif key in {"ctrl-c", "ctrl-d", "ctrl-z"} | escape_sequences:
                show_cursor(True)
                raise TeletypeQuitException
            elif key == "space":
                self._select_line()
            elif key == "lf":
                break
        if self.erase_screen:
            erase_screen()
        else:
            move_cursor(rows=len(self.choices) - self._line + 1)
        show_cursor(True)
        return self.selected

    def _move_line(self, distance):
        offset = (self._line + distance) % len(self.choices) - self._line
        if offset == 0:
            return
        self._line += offset
        print(" ", end="")
        move_cursor(rows=offset, cols=-1)
        print("%s" % _chars["cursor"], end="")
        move_cursor(cols=-1)

    def _select_line(self):
        self._selected_lines ^= {self._line}
        move_cursor(cols=1)
        print(
            _chars[
                "filled" if self._line in self._selected_lines else "unfilled"
            ],
            end="",
        )
        move_cursor(cols=-2)

    @property
    def selected(self):
        return [
            self.choices[line % len(self.choices)]
            for line in self._selected_lines
        ]


class ProgressBar:
    def __init__(self, width=80, header=""):
        self.width = width
        self.header = header

    def process(self, iterable, total=None):
        try:
            steps = total or len(iterable)
        except AttributeError:
            raise TeletypeException("Unable to determine range")
        show_cursor(False)
        self.update(0, steps)
        skip_count = max(steps // 100, 1)
        for step, _ in enumerate(iterable, 1):
            if step % skip_count == 0 or step == steps:
                self.update(step, steps)
        show_cursor(True)
        print()

    def update(self, step, steps):
        prefix = ""
        if self.header:
            prefix += "%s: " % style_format(self.header, "bold")
        format_specifier = "%%0%dd" % len(str(steps))
        prefix += "%s/%d " % (format_specifier % step, steps)
        prefix += style_format("|", ("magenta", "bold"))
        percent = step / steps * 100
        suffix = style_format("|", ("magenta", "bold")) + " %03d%%" % percent
        units_total = max(self.width - len(strip_format(prefix + suffix)), 5)
        units = units_total * step // steps
        line = (
            prefix
            + units * style_format(u"█", "green")
            + (units_total - units) * " "
            + suffix
        )
        print("\r%s" % line, end="")
