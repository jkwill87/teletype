# coding=utf-8

from __future__ import print_function

from ..exceptions import TeletypeException
from ..io import show_cursor, strip_format, style_format
from .config import get_glyph


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
        g_block = get_glyph("block")
        g_edge = get_glyph("edge")
        prefix = ""
        if self.header:
            prefix += "%s: " % style_format(self.header, "bold")
        format_specifier = "%%0%dd" % len(str(steps))
        prefix += "%s/%d %s" % (format_specifier % step, steps, g_edge)
        suffix = g_edge + " %03d%%" % (step / steps * 100)
        units_total = max(self.width - len(strip_format(prefix + suffix)), 5)
        units = units_total * step // steps
        line = prefix + units * g_block + (units_total - units) * " " + suffix
        print("\r%s" % line, end="")
