# coding=utf-8

from ctypes import windll

__all__ = ["CHARS_DEFAULT", "SCAN_CODES"]

# Allows Windows 10 Anniversary (build>=16257) to use VT100 Codes
# https://docs.microsoft.com/windows/console/console-virtual-terminal-sequences
windll.kernel32.SetConsoleMode(windll.kernel32.GetStdHandle(-11), 1 | 2 | 4 | 8)

CHARS_DEFAULT = {
    "arrow": u"►",
    "block": u"█",
    "left-edge": u"▐",
    "right-edge": u"▌",
    "selected": u"●",
    "unselected": u"○",
}

SCAN_CODES = {
    13: "\r",
    27: "\x1b",
    15104: "\x1bOP",
    15360: "\x1bOQ",
    15616: "\x1bOR",
    15872: "\x1bOS",
    16128: "\x1bO15~",
    16384: "\x1bO17~",
    16640: "\x1bO18~",
    16896: "\x1bO19~",
    17152: "\x1bO20~",
    17408: "\x1bO21~",
    18400: "\x1b[H",
    18656: "\x1b[A",
    18912: "\x1b[5~",
    19424: "\x1b[D",
    19936: "\x1b[C",
    20448: "\x1b[F",
    20704: "\x1b[B",
    20960: "\x1b[6~",
    21216: "\x1b[2~",
    21472: "\x1b[3~",
    22272: "\x1bO23~",
    34528: "\x1bO24~",
}
