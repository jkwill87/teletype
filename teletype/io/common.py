from __future__ import print_function

from re import sub
from sys import stdout
from .. import codes


def erase_lines(n=1):
    """ Erases n lines from the screen and moves the cursor up to follow
    """
    for _ in range(n):
        print(codes.cursor["up"], end="")
        print(codes.cursor["eol"], end="")


def erase_screen():
    """ Clears all text from the screen
    """
    print(codes.cursor["clear"], end="")


def move_cursor(cols=0, rows=0):
    """ Moves the cursor the given number of columns and rows
    
    The cursor is moved right when cols is positive and left when negative.
    The cursor is moved down when rows is positive and down when negative.
    """
    if cols == 0 and rows == 0:
        return
    commands = ""
    commands += codes.cursor["up" if rows < 0 else "down"] * abs(rows)
    commands += codes.cursor["left" if cols < 0 else "right"] * abs(cols)
    if commands:
        print(commands, end="")
        stdout.flush()


def show_cursor():
    """ Shows the cursor indicator
    """
    print(codes.cursor["show"], end="")


def hide_cursor():
    """ Hides the cursor indicator; remember to call show_cursor before exiting
    """
    print(codes.cursor["hide"], end="")


def strip_format(text):
    """ Returns text with all control sequences removed
    """
    return sub(r"(\x9B|\x1B\[)[0-?]*[ -/]*[@-~]", "", text)


def style_format(text, style):
    """ Wraps texts in terminal control sequences

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
        prefix += codes.colours.get(s, "")
        prefix += codes.highlights.get(s, "")
        prefix += codes.modes.get(s, "")
    return prefix + text + codes.modes["reset"]


def style_print(*values, **kwargs):
    """ A convenience function that applies style_format to text before printing
    """
    style = kwargs.pop("style", None)
    values = [style_format(value, style) for value in values]
    print(*values, **kwargs)
