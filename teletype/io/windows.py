from msvcrt import getch, kbhit  # pylint: disable=E0401

from colorama import colorama_text

from ..codes import scan_codes, keys_flipped


def get_key(raw=False):
    while True:
        if kbhit():
            char = getch()
            ordinal = ord(char)
            if 0 < ordinal < 225:
                extention = ord(getch())
                scan_code = ordinal + extention * 256
                result = scan_codes.get(scan_code)
                break
            else:
                result = char.decode()
                break
    return result if raw else keys_flipped.get(result, result)
