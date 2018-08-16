from __future__ import print_function

from curses import setupterm, tigetstr
from re import sub
from sys import stdin
from termios import TCSADRAIN, tcgetattr, tcsetattr
from tty import setraw
import sys
from teletype import codes

setupterm()

posix_term_codes = {
    direction: sub(r"\$<\d+>[/*]?", "", (tigetstr(descriptor) or b"").decode())
    for direction, descriptor in (
        ("up", "cuu1"),
        ("down", "cud1"),
        ("left", "cub1"),
        ("right", "cuf1"),
        ("bol", "el1"),
        ("eol", "el"),
        ("clear_screen", "clear"),
        ("hide_cursor", "civis"),
        ("show_cursor", "cnorm"),
    )
}


def get_key(raw=False):
    file_descriptor = stdin.fileno()
    state = tcgetattr(file_descriptor)
    chars = []
    try:
        setraw(stdin.fileno())
        for i in range(3):
            char = stdin.read(1)
            ordinal = ord(char)
            chars.append(char)
            if i == 0 and ordinal != 27:
                break
            elif i == 1 and ordinal != 91:
                break
            elif i == 2 and ordinal != 51:
                break
    finally:
        tcsetattr(file_descriptor, TCSADRAIN, state)
    result = "".join(chars)
    return result if raw else codes.keys_flipped.get(result, result)


def move_cursor(cols=0, rows=0):
    if cols == 0 and rows == 0:
        return
    commands = ""
    commands += posix_term_codes["up" if rows < 0 else "down"] * abs(rows)
    commands += posix_term_codes["left" if cols < 0 else "right"] * abs(cols)
    if commands:
        print(commands, end="")
        sys.stdout.flush()


def show_cursor(visible=True):
    print(posix_term_codes["show_cursor" if visible else "hide_cursor"], end="")


def erase_lines(n=1):
    for _ in range(n):
        print(posix_term_codes["up"], end="")
        print(posix_term_codes["eol"], end="")


def erase_screen():
    print(posix_term_codes["clear_screen"], end="")


def strip_format(text):
    return sub(r"(\x9B|\x1B\[)[0-?]*[ -/]*[@-~]", "", text)
