import os
from typing import Optional

from teletype import codes, io

__all__ = [
    "SelectOne",
    "SelectApproval",
    "SelectMany",
    "ProgressBar",
    "ChoiceHelper",
]


class SelectOne:
    """Allows the user to make a single selection

    - Use arrow keys or 'j' and 'k' to highlight selection
    - Press mnemonic keys to move to ChoiceHelper, another time to submit
    - Use return key to submit
    """

    _multiselect = False

    def __init__(self, choices, **chars):
        self.chars = codes.CHARS_DEFAULT.copy()
        self.chars.update(chars)
        self._mnemonics = {}
        self._choices = []
        for choice in choices:
            if choice in self._choices:
                continue
            self._choices.append(choice)
            if isinstance(choice, ChoiceHelper) and choice.mnemonic:
                self._mnemonics[choice.mnemonic] = len(self._mnemonics)
        self._line = 0
        self._selected_lines = set()

    def __len__(self):
        return len(self.choices)

    def __hash__(self):
        return self.choices.__hash__()

    def _display_choice(self, idx, choice):
        print(" %s %s" % (self.chars["arrow"] if idx == 0 else " ", choice))

    def _select_line(self):
        self._selected_lines ^= {self._line}
        io.move_cursor(cols=1)
        if self._line in self._selected_lines:
            char = self.chars["selected"]
        else:
            char = self.chars["unselected"]
        print(char, end=None)
        io.move_cursor(cols=-2)

    def _move_line(self, distance):
        col_offset = 1 if self._multiselect else 2
        g_cursor = self.chars["arrow"]
        offset = (self._line + distance) % len(self.choices) - self._line
        if offset == 0:
            return 0
        self._line += offset
        print(" " * col_offset, end=None)
        io.move_cursor(rows=offset, cols=-col_offset)
        print("%s%s" % (" " * (col_offset - 1), g_cursor), end=None)
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
                choice_count = len(self.choices)
                mnemonic_count = len(self._mnemonics)
                mnemonic_idx = self._mnemonics[key]
                dist = choice_count - mnemonic_count - self._line + mnemonic_idx
                self._move_line(dist)
                if dist == 0:
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
    def choices(self):
        """Returns read-only tuple of choices"""
        return tuple(self._choices)

    @property
    def highlighted(self):
        """Returns the value for the currently highlighted choice"""
        choice = self.choices[self._line % len(self.choices)]
        return self._strip_choice(choice)

    @property
    def selected(self):
        """Returns the values for all currently selected choices"""
        return tuple(
            self._strip_choice(self.choices[line % len(self.choices)])
            for line in self._selected_lines
        )

    def prompt(self):
        self._line = 0
        self._selected_lines = set()
        if not self.choices:
            return None
        i = 0
        for i, choice in enumerate(self.choices):
            self._display_choice(i, choice)
        io.move_cursor(rows=-1 * i - 1)
        io.hide_cursor()
        try:
            self._process_keypress()
        finally:
            io.show_cursor()
            io.move_cursor(rows=len(self.choices) - self._line)
        return self.selected if self._multiselect else self.highlighted


class SelectApproval(SelectOne):
    """Simple extension of SelectOne offering the option of selecting yes or no"""

    def __init__(self, **chars):
        yes = ChoiceHelper(True, "yes", None, "y")
        no = ChoiceHelper(False, "no", None, "n")
        SelectOne.__init__(self, (yes, no), **chars)


class SelectMany(SelectOne):
    """Allows users to select multiple items using

    - Use arrow keys or 'j' and 'k' to highlight selection
    - Press mnemonic keys to move to ChoiceHelper, another time to toggle
    - Use space key to toggle selection
    - Use return key to submit
    """

    _multiselect = True

    def _display_choice(self, idx, choice):
        s = "%s%s %s " % (
            " " if idx else self.chars["arrow"],
            self.chars["unselected"],
            choice,
        )
        print(s)


class ProgressBar:
    """Displays a progress bar"""

    def __init__(self, label, width=None, **chars):
        self.label = label
        self.width = width
        self.chars = codes.CHARS_DEFAULT.copy()
        self.chars.update(chars)

    def process(self, iterable, steps):
        """Iterates over an object, updating the progress bar on each iteration"""
        io.hide_cursor()
        self.update(0, steps)
        skip_count = max(steps // 1000, 1)
        for step, _ in enumerate(iterable, 1):
            if step % skip_count == 0 or step == steps:
                self.update(step, steps)
        io.show_cursor()

    def update(self, step, steps):
        """Manually updates the progress bar"""
        try:
            # Python 3.3+ only
            width = self.width or os.get_terminal_size().columns
        except (AttributeError, OSError):
            width = 80

        prefix = "%s: " % self.label
        format_specifier = "%%0%dd" % len(str(steps))
        prefix += "%s/%d%s" % (
            format_specifier % step,
            steps,
            self.chars["left-edge"],
        )
        suffix = self.chars["right-edge"] + "%03d%%" % (step / steps * 100)
        units_total = max(width - len(io.strip_format(prefix + suffix)), 5)
        units = units_total * step // steps
        line = (
            prefix + units * self.chars["block"] + (units_total - units) * " " + suffix
        )
        io.erase_lines()
        print("\r%s" % line)


class ChoiceHelper:
    """Helper class for packaging and displaying objects as choices"""

    def __init__(self, value, label=None, style=None, mnemonic=None):
        self._idx = -1
        self._bracketed = False
        self._str = label or str(value).strip()
        self.value = value
        self.label = label
        style = style or ""
        self.style = style if isinstance(style, str) else " ".join(style)
        self._mnemonic = ""
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
        elif self._bracketed:
            s = "%s[%s]%s" % (
                self._str[: self._idx],
                self._str[self._idx],
                self._str[self._idx + 1 :],
            )
            s = io.style_format(s, self.style)
        else:
            s = (
                io.style_format(self._str[: self._idx], self.style)
                + io.style_format(self._str[self._idx], "underline " + self.style)
                + io.style_format(self._str[self._idx + 1 :], self.style)
            )
        return s

    @property
    def mnemonic(self) -> Optional[str]:
        return self._mnemonic

    @mnemonic.setter
    def mnemonic(self, m: Optional[str]):
        if not m:
            self._mnemonic = None
            return
        line_len = len(m) if isinstance(m, str) else 0
        if not line_len:
            self._bracketed = False
            self._mnemonic = None
            self._idx = -1
        elif line_len == 1:
            self._mnemonic = m
            self._bracketed = False
            self._idx = self._str.lower().find(self._mnemonic.lower())
        elif line_len == 3 and m[0] == "[" and m[2] == "]":
            self._mnemonic = m[1]
            self._bracketed = True
            self._idx = self._str.lower().find(self._mnemonic.lower())
        else:
            raise ValueError("mnemonic must be None or of form 'x' or '[x]'")
        if self._mnemonic not in (self.label or str(self.value)):
            raise ValueError("mnemonic not present in value or label")
