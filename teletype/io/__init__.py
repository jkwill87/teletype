from __future__ import print_function

from os import name

from teletype import codes

if name in ("nt", "cygwin"):
    from teletype.io.windows import *
else:
    from teletype.io.unix import *


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
    return prefix + text + codes.reset


def style_print(*values, **kwargs):
    style = kwargs.pop("style", None)
    values = [style_format(value, style) for value in values]
    print(*values, **kwargs)
