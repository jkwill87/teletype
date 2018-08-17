# coding=utf-8

from __future__ import print_function

from ..codes import escape_sequences
from ..exceptions import TeletypeQuitException, TeletypeSkipException
from ..io import (
    erase_screen,
    get_key,
    move_cursor,
    show_cursor,
    strip_format,
    style_format,
    style_print,
)
from .config import get_glyph



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
