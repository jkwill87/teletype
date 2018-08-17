# coding=utf-8

from __future__ import print_function

from ..codes import escape_sequences
from ..exceptions import (
    TeletypeException,
    TeletypeQuitException,
    TeletypeSkipException,
)
from ..io import (
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
