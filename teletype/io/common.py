from re import sub
from sys import stdout
from typing import Any, Optional

from teletype import codes
from teletype.typedef import TSTYLE

__all__ = [
    "erase_lines",
    "erase_screen",
    "hide_cursor",
    "move_cursor",
    "show_cursor",
    "strip_format",
    "style_format",
    "style_print",
    "style_input",
]


def erase_lines(n: int = 1):
    """Erases n lines from the screen and moves the cursor up to follow"""
    for _ in range(n):
        print(codes.CURSOR["up"], end="")
        print(codes.CURSOR["eol"], end="")
    stdout.flush()


def erase_screen():
    """Clears all text from the screen"""
    print(codes.CURSOR["clear"], end="")
    stdout.flush()


def move_cursor(cols: int = 0, rows: int = 0):
    """Moves the cursor the given number of columns and rows

    The cursor is moved right when cols is positive and left when negative.
    The cursor is moved down when rows is positive and down when negative.
    """
    if cols == 0 and rows == 0:
        return
    commands = ""
    commands += codes.CURSOR["up" if rows < 0 else "down"] * abs(rows)
    commands += codes.CURSOR["left" if cols < 0 else "right"] * abs(cols)
    if commands:
        print(commands, end="")
        stdout.flush()


def show_cursor():
    """Shows the cursor indicator"""
    print(codes.CURSOR["show"], end="")
    stdout.flush()


def hide_cursor():
    """Hides the cursor indicator; remember to call show_cursor before exiting"""
    print(codes.CURSOR["hide"], end="")
    stdout.flush()


def strip_format(text: str) -> str:
    """Returns text with all control sequences removed"""
    return sub(r"(\x9B|\x1B\[)[0-?]*[ -/]*[@-~]", "", text)


def style_format(text: str, style: TSTYLE = None, reset: bool = True) -> str:
    """Wraps texts in terminal control sequences

    Style can be passed as either a collection or space delimited string.
    Valid styles can be found in the codes module. Invalid or unsuported styles
    will just be ignored.
    """
    if not style:
        return text
    if isinstance(style, str):
        style = style.split(" ")
    prefix = ""
    for s in style:
        prefix += codes.COLOURS.get(s, "")
        prefix += codes.HIGHLIGHTS.get(s, "")
        prefix += codes.MODES.get(s, "")
    if reset:
        text += codes.MODES["reset"]
    return prefix + text


def style_print(*values: Any, **options: Any):
    """A convenience function that applies style_format to text before printing"""
    style = options.pop("style", None)
    values = tuple(style_format(value, style) for value in values)
    print(*values, **options)


def style_input(prompt: Optional[str] = None, style: TSTYLE = None) -> str:
    """A convenience function that applies style_format before get user input"""
    if prompt and style:
        prompt = style_format(prompt, style)
    return input(prompt)
