# coding=utf-8

from __future__ import print_function

import os

from ..exceptions import TeletypeException
from ..io import hide_cursor, show_cursor, strip_format, style_format
from .config import _get_glyph


class ProgressBar:
    def __init__(self, width=None, header=""):
        self.width = width
        self.header = header
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
        hide_cursor()
        self.update(0, steps)
        skip_count = max(steps // 1000, 1)
        for step, _ in enumerate(iterable, 1):
            if step % skip_count == 0 or step == steps:
                self.update(step, steps)
        show_cursor()
        print()

    def update(self, step, steps):
        g_block = _get_glyph("block")
        g_l_edge = _get_glyph("left-edge")
        g_r_edge = _get_glyph("right-edge")
        prefix = ""
        if self.header:
            prefix += "%s: " % style_format(self.header, "bold")
        format_specifier = "%%0%dd" % len(str(steps))
        prefix += "%s/%d%s" % (format_specifier % step, steps, g_l_edge)
        suffix = g_r_edge + "%03d%%" % (step / steps * 100)
        units_total = max(self.width - len(strip_format(prefix + suffix)), 5)
        units = units_total * step // steps
        line = prefix + units * g_block + (units_total - units) * " " + suffix
        print("\r%s" % line, end="")
