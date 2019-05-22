# coding=utf-8

from msvcrt import getch, kbhit  # pylint: disable=E0401

from teletype.codes import KEYS_FLIPPED, SCAN_CODES


def get_key(raw=False):
    """ Gets a single key from stdin
    """
    while True:
        try:
            if kbhit():
                char = getch()
                ordinal = ord(char)
                if ordinal in (0, 224):
                    extention = ord(getch())
                    scan_code = ordinal + extention * 256
                    result = SCAN_CODES.get(scan_code)
                    break
                else:
                    result = char.decode()
                    break
        except KeyboardInterrupt:
            return "ctrl-c"
    return result if raw else KEYS_FLIPPED.get(result, result)
