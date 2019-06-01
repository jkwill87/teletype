# coding=utf-8

from __future__ import print_function

import os
from abc import ABCMeta, abstractmethod
from copy import deepcopy

from teletype import codes, io

__all__ = [
    "SelectOne",
    "SelectApproval",
    "SelectMany",
    "ProgressBar",
    "ChoiceHelper",
]

_AbstractClass = ABCMeta("ABC", (object,), {"__slots__": ()})


class _Component(_AbstractClass):
    """ Base class for all components
    """

    def __init__(
        self,
        header,
        style_primary="green",
        style_secondary="dark green",
        display_chars=None,
        erase_screen=False,
    ):
        self.header = header
        self.style_primary = style_primary
        self.style_secondary = style_secondary
        self.display_chars = display_chars or deepcopy(codes.DEFAULT_CHARS)
        self.erase_screen = erase_screen

    def __str__(self):
        return io.strip_format(self.header)

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

    _multiselect = False

    def __init__(
        self,
        choices,
        header,
        style_primary="green",
        style_secondary="dark green",
        display_chars=None,
        erase_screen=False,
    ):
        _Component.__init__(
            self,
            header,
            style_primary,
            style_secondary,
            display_chars,
            erase_screen,
        )
        self.choices = []
        self._mnemonics = {}
        for choice in choices:
            if choice in self.choices:
                continue
            self.choices.append(choice)
            if isinstance(choice, ChoiceHelper) and choice.mnemonic:
                self._mnemonics[choice.mnemonic] = len(self._mnemonics)
        self._line = 0
        self._selected_lines = set()

    def __len__(self):
        return len(self.choices)

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
        col_offset = 1 if self._multiselect else 2
        g_cursor = self._get_glyph("arrow")
        offset = (self._line + distance) % len(self.choices) - self._line
        if offset == 0:
            return 0
        self._line += offset
        print(" " * col_offset, end="")
        io.move_cursor(rows=offset, cols=-col_offset)
        print("%s%s" % (" " * (col_offset - 1), g_cursor), end="")
        io.move_cursor(cols=-col_offset)
        return offset

    def _process_keypress(self):
        while True:
            key = io.get_key()
            # navigation key pressed; vim keys allowed when mnemonics not in use
            if key == "up" or (key == "k" and not self._mnemonics):
                self._move_line(-1)
            elif key == "down" or (key == "j" and not self._mnemonics):
                self._move_line(1)
            # space pressed
            elif self._multiselect and key == "space":
                self._select_line()
            # enter pressed
            elif key in ("lf", "nl"):
                break
            # mnemonic pressed
            elif self._mnemonics.get(key) is not None:
                distance = self._mnemonics[key] - self._line
                self._move_line(distance)
                if distance == 0:
                    # on second keypress...
                    if self._multiselect:
                        self._select_line()
                    else:
                        break
            # escape sequences pressed
            elif key in {"ctrl-c", "ctrl-d", "ctrl-z"} | codes.ESCAPE_SEQUENCES:
                raise KeyboardInterrupt("%s pressed" % key)

    @staticmethod
    def _strip_choice(choice):
        if isinstance(choice, str):
            return io.strip_format(choice)
        if isinstance(choice, ChoiceHelper):
            return choice.value
        return choice

    @property
    def highlighted(self):
        """ Returns the value for the currently highlighted choice
        """
        choice = self.choices[self._line % len(self.choices)]
        return self._strip_choice(choice)

    @property
    def selected(self):
        """ Returns the values for all currently selected choices
        """
        return tuple(
            self._strip_choice(self.choices[line % len(self.choices)])
            for line in self._selected_lines
        )

    def prompt(self):
        self._line = 0
        self._selected_lines = set()
        if not self.choices:
            return None
        if self.erase_screen:
            io.erase_screen()
        if self.header:
            print(self.header)
        i = 0
        for i, choice in enumerate(self.choices):
            self._display_choice(i, choice)
        io.move_cursor(rows=-1 * i - 1)
        io.hide_cursor()
        try:
            self._process_keypress()
        finally:
            io.show_cursor()
            if self.erase_screen:
                io.erase_screen()
            else:
                io.move_cursor(rows=len(self.choices) - self._line)
        return self.selected if self._multiselect else self.highlighted

    @abstractmethod
    def _display_choice(self, idx, choice):
        pass


class SelectOne(_Select):
    """ Allows the user to make a single selection

    - Use arrow keys or 'j' and 'k' to highlight selection
    - Press mnemonic keys to move to ChoiceHelper, another time to submit
    - Use return key to submit
    """

    _multiselect = False

    def _display_choice(self, idx, choice):
        g_arrow = self._get_glyph("arrow")
        print(" %s %s" % (g_arrow if idx == 0 else " ", choice))


class SelectApproval(SelectOne):
    """ Simple extension of SelectOne offering the option of selecting yes or no
    """

    def __init__(
        self,
        header,
        style_primary="green",
        style_secondary="dark green",
        display_chars=None,
        erase_screen=False,
    ):
        yes = ChoiceHelper(True, "yes", None, "y")
        no = ChoiceHelper(False, "no", None, "n")
        SelectOne.__init__(
            self,
            (yes, no),
            header,
            style_primary,
            style_secondary,
            display_chars,
            erase_screen,
        )


class SelectMany(_Select):
    """ Allows users to select multiple items using

    - Use arrow keys or 'j' and 'k' to highlight selection
    - Press mnemonic keys to move to ChoiceHelper, another time to toggle
    - Use space key to toggle selection
    - Use return key to submit
    """

    _multiselect = True

    def _display_choice(self, idx, choice):
        g_arrow = self._get_glyph("arrow")
        g_unselected = self._get_glyph("unselected")
        print("%s%s %s " % (" " if idx else g_arrow, g_unselected, choice))


class ProgressBar(_Component):
    """ Displays a progress bar
    """

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
        try:
            # Python 3.3+ only
            width = os.get_terminal_size().columns
        except (AttributeError, OSError):
            width = 80

        prefix = ""
        if self.header:
            prefix += "%s: " % io.style_format(self.header, "bold")
        format_specifier = "%%0%dd" % len(str(steps))
        prefix += "%s/%d%s" % (format_specifier % step, steps, g_l_edge)
        suffix = g_r_edge + "%03d%%" % (step / steps * 100)
        units_total = max(width - len(io.strip_format(prefix + suffix)), 5)
        units = units_total * step // steps
        line = prefix + units * g_block + (units_total - units) * " " + suffix
        print("\r%s" % line, end="")


class ChoiceHelper(object):
    """ Helper class for packaging and displaying objects as choices
    """

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
        r = "ChoiceHelper(%r" % self.value
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
