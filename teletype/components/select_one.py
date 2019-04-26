# coding=utf-8

from __future__ import print_function

from teletype.io import erase_lines
from ..codes import escape_sequences
from ..exceptions import TeletypeQuitException, TeletypeSkipException
from ..io import (
    erase_screen,
    get_key,
    hide_cursor,
    move_cursor,
    show_cursor,
    strip_format,
    style_format,
    style_print,
)
from .config import _get_glyph


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
        if options.get("skip") is True:
            self.skip = True
            self.choices.append(style_format("[s]kip", "dark"))
        else:
            self.skip = False
        if options.get("quit") is True:
            self.quit = True
            self.choices.append(style_format("[q]uit", "dark"))
        else:
            self.quit = False

    def prompt(self):
        self._line = 0
        g_cursor = _get_glyph("arrow")
        if not self.choices:
            return
        hide_cursor()
        if self.erase_screen:
            erase_screen()
        if self.header:
            style_print(self.header, style="bold")
        for i, choice in enumerate(self.choices):
            print(" %s %s" % (g_cursor if i == 0 else " ", choice))
        move_cursor(rows=-1 * i - 1)
        while True:
            key = get_key()
            if key in {"up", "k"}:
                self._move_line(-1)
            elif key in {"down", "j"}:
                self._move_line(1)
            elif key in {"ctrl-c", "ctrl-d", "ctrl-z"} | escape_sequences:
                move_cursor(0, len(self.choices) - self._line)
                show_cursor()
                raise TeletypeQuitException
            elif key == "s" and self.skip:
                distance = len(self.choices) - self._line - 1
                if self.quit:
                    distance -= 1
                if not self._move_line(distance):
                    break
            elif key == "q" and self.quit:
                distance = len(self.choices) - self._line - 1
                if not self._move_line(distance):
                    break
            elif key in ("lf", "nl"):
                break
        if self.erase_screen:
            erase_screen()
        else:
            move_cursor(rows=len(self.choices) - self._line)
        show_cursor()
        if self.quit and self.selected == "[q]uit":
            raise TeletypeQuitException
        elif self.skip and self.selected == "[s]kip":
            raise TeletypeSkipException
        return self.selected

    def _move_line(self, distance):
        g_cursor = _get_glyph("arrow")
        offset = (self._line + distance) % len(self.choices) - self._line
        if offset == 0:
            return 0
        self._line += offset
        print("  ", end="")
        move_cursor(rows=offset, cols=-2)
        print(" %s" % g_cursor, end="")
        move_cursor(cols=-2)
        return offset

    @property
    def selected(self):
        choice = self.choices[self._line % len(self.choices)]
        if isinstance(choice, str):
            choice = strip_format(choice)
        return choice
