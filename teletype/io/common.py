from __future__ import print_function

from re import sub
from sys import stdout
from .. import codes


def erase_lines(n=1):
    for _ in range(n):
        print(codes.cursor["up"], end="")
        print(codes.cursor["eol"], end="")


def erase_screen():
    print(codes.cursor["clear"], end="")


def move_cursor(cols=0, rows=0):
    if cols == 0 and rows == 0:
        return
    commands = ""
    commands += codes.cursor["up" if rows < 0 else "down"] * abs(rows)
    commands += codes.cursor["left" if cols < 0 else "right"] * abs(cols)
    if commands:
        print(commands, end="")
        stdout.flush()


def show_cursor():
    print(codes.cursor["show"], end="")


def hide_cursor():
    print(codes.cursor["hide"], end="")


def strip_format(text):
    return sub(r"(\x9B|\x1B\[)[0-?]*[ -/]*[@-~]", "", text)


def style_format(text, style):
    if not style:
        return text
    if isinstance(style, str):
        style = (style,)
    prefix = ""
    for s in style:
        prefix += codes.colours.get(s, "")
        prefix += codes.highlights.get(s, "")
        prefix += codes.modes.get(s, "")
    return prefix + text + codes.modes["reset"]


def style_print(*values, **kwargs):
    style = kwargs.pop("style", None)
    values = [style_format(value, style) for value in values]
    print(*values, **kwargs)
