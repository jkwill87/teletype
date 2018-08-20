from __future__ import print_function

from sys import stdin
from termios import TCSADRAIN, tcgetattr, tcsetattr  # pylint: disable=E0401
from tty import setraw

from .. import codes


def get_key(raw=False):
    """ Gets a single key from stdin
    """
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
