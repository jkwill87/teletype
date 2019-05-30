# coding=utf-8

from __future__ import print_function

import os
from copy import deepcopy

from teletype import codes, io

__all__ = ["SelectOne", "SelectApproval", "SelectMany", "ProgressBar", "Choice"]


class _Component(object):
    """ Base class for all components
    """

    def __init__(self, **config):
        self._backups = ()
        self.display_chars = config.get(
            "display_chars", deepcopy(codes.DEFAULT_CHARS)
        )
        self.erase_screen = config.get("erase_screen", False)
        self.header = config.get("header", "").strip()
        self.style_primary = config.get("style_primary", "green")
        self.style_secondary = config.get("style_secondary", "dark green")

    def _get_char_category(self, key):
        for category, d in self.display_chars.items():
            if key in d.keys():
                return category
        raise KeyError

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

    def char_set(self, key, value):
        """ Updates charters used to render components.
        """
        category = self._get_char_category(key)
        if not category:
            raise KeyError
        self.display_chars[category][key] = value


class _Select(_Component):
    """ Base class for selection components
    """

    def __init__(self, choices, **config):
        _Component.__init__(self, **config)
        unique_choices = set()
        self.choices = []
        for choice in choices:
            if choice not in unique_choices:
                unique_choices.add(choice)
                self.choices.append(choice)
        self._line = 0
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

    def _get_selection(self, multiselect=False):
        io.hide_cursor()
        err = None
        while True:
            key = io.get_key()
            # navigation key pressed
            if key in {"up", "k"}:
                self._move_line(-1)
            elif key in {"down", "j"}:
                self._move_line(1)
            # space pressed
            elif multiselect and key == "space":
                self._select_line()
            # enter pressed
            elif key in ("lf", "nl"):
                break
            # escape sequences pressed
            elif key in {"ctrl-c", "ctrl-d", "ctrl-z"} | codes.ESCAPE_SEQUENCES:
                err = KeyboardInterrupt("%s pressed" % key)
                break
        io.show_cursor()
        if self.erase_screen:
            io.erase_screen()
        else:
            io.move_cursor(rows=len(self.choices) - self._line)
        if err:
            raise err  # pylint: disable=raising-bad-type

    @property
    def highlighted(self):
        """ Returns the value for the currently highlighted choice
        """
        choice = self.choices[self._line % len(self.choices)]
        if isinstance(choice, str):
            choice = io.strip_format(choice)
        return choice

    @property
    def selected(self):
        """ Returns the values for all currently selected choices
        """
        return tuple(
            self.choices[line % len(self.choices)]
            for line in self._selected_lines
        )


class SelectOne(_Select):
    """ Allows the user to make a single selection

    - Use arrow keys or 'j' and 'k' to highlight selection
    - Use return key to submit
    """

    def __init__(self, choices, **config):
        _Select.__init__(self, choices, **config)
        self._col_offset = 2

    def prompt(self):
        """ Displays choices to user and prompts them for their selection
        """
        self._line = 0
        g_cursor = self._get_glyph("arrow")
        if not self.choices:
            return None
        if self.erase_screen:
            io.erase_screen()
        if self.header:
            print(self.header)
        for i, choice in enumerate(self.choices):
            print(" %s %s" % (g_cursor if i == 0 else " ", choice))
        io.move_cursor(rows=-1 * i - 1)
        self._get_selection()
        return self.highlighted


class SelectApproval(SelectOne):
    """ Simple extension of SelectOne offering the option of selecting yes or no
    """

    def __init__(self, **config):
        SelectOne.__init__(self, ("yes", "no"), **config)


class SelectMany(_Select):
    """ Allows users to select multiple items using

    - Use arrow keys or 'j' and 'k' to highlight selection
    - Use space key to toggle selection
    - Use return key to submit
    """

    def prompt(self):
        """ Displays choices to user and prompts them for their selection(s)
        """
        self._line = 0
        self._selected_lines = set()
        g_arrow = self._get_glyph("arrow")
        g_unselected = self._get_glyph("unselected")
        if not self.choices:
            return tuple()
        if self.erase_screen:
            io.erase_screen()
        if self.header:
            print(self.header)
        for i, choice in enumerate(self.choices):
            print("%s%s %s " % (" " if i else g_arrow, g_unselected, choice))
        io.move_cursor(rows=-1 * i - 1)
        self._get_selection(multiselect=True)
        return self.selected


class ProgressBar(_Component):
    """ Displays a progress bar
    """

    def __init__(self, **config):
        _Component.__init__(self, **config)
        try:
            # Python 3.3+ only
            self.width = config.get("width", os.get_terminal_size().columns)
        except (AttributeError, OSError):
            self.width = 80

    def process(self, iterable, steps):
        """ Iterates over an object, updating the progress bar on each iteration
        """
        io.hide_cursor()
        self.update(0, steps)
        skip_count = max(steps // 1000, 1)
        for step, _ in enumerate(iterable, 1):
            if step % skip_count == 0 or step == steps:
                self.update(step, steps)
        io.show_cursor()
        print()

    def update(self, step, steps):
        """ Manually updates the progress bar
        """
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


class Choice(object):
    def __init__(self, value, label=None, style=None, mnemonic=None):
        self._idx = -1
        self._mnemonic = False
        self._bracketted = False
        self._str = label or str(value).strip()
        self.value = value
        self.label = label
        style = style or ""
        self.style = style if isinstance(style, str) else " ".join(style)
        self.mnemonic = mnemonic

    def __repr__(self):
        r = "Choice(%r" % self.value
        if self.label:
            r += ", %r" % self.label
        if self.style:
            r += ", %r" % self.style
        if self.mnemonic:
            r += ", %r" % self.mnemonic
        r += ")"
        return r

    def __str__(self):
        if self._idx < 0:
            s = io.style_format(self._str, self.style)
        elif self._bracketted:
            s = "%s[%s]%s" % (
                self._str[: self._idx],
                self._str[self._idx],
                self._str[self._idx + 1 :],
            )
            s = io.style_format(s, self.style)
        else:
            s = (
                io.style_format(self._str[: self._idx], self.style)
                + io.style_format(
                    self._str[self._idx], "underline " + self.style
                )
                + io.style_format(self._str[self._idx + 1 :], self.style)
            )
        return s

    @property
    def mnemonic(self):
        return self._mnemonic

    @mnemonic.setter
    def mnemonic(self, m):
        l = len(m) if isinstance(m, str) else 0
        if not l:
            self._bracketted = False
            self._mnemonic = None
            self._idx = -1
        elif l == 1:
            self._mnemonic = m
            self._bracketted = False
            self._idx = self._str.lower().find(self.mnemonic.lower())
        elif l == 3 and m[0] == "[" and m[2] == "]":
            self._mnemonic = m[1]
            self._bracketted = True
            self._idx = self._str.lower().find(self.mnemonic.lower())
        else:
            raise ValueError("mnemonic must be None or of form 'x' or '[x]'")
