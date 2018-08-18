# coding=utf-8

from ..io import style_format as _style_format

# These variables control module internal state; please do not modify directly
_backups = ()
_ascii_mode = False
_primary_style = ("blue",)
_secondary_style = ("magenta", "bold")
_chars = {
    "primary": {"selected": u"●", "block": u"█"},
    "secondary": {"arrow": u"❯", "edge": "|"},
    "plain": {"unselected": u"○"},
}


def _get_char_category(key):
    for category, d in _chars.items():
        if key in d.keys():
            return category


def set_style(primary=None, secondary=None):
    """
    """
    if primary:
        _primary_style = primary
    if secondary:
        _secondary_style = secondary


def set_char(key, value):
    """
    """
    category = _get_char_category(key)
    if not category:
        raise KeyError
    _chars[category][key] = value


def get_glyph(key):
    """
    """
    category = _get_char_category(key)
    if not category:
        raise KeyError
    glyph = _chars[category][key]
    if category == "primary":
        glyph = _style_format(glyph, _primary_style)
    elif category == "secondary":
        glyph = _style_format(glyph, _secondary_style)
    return glyph


def ascii_mode(enabled=True):
    """
    """
    global _backups, _chars, _primary_style, _secondary_style, _ascii_mode
    if not (enabled or _backups) or (enabled and _ascii_mode):
        return
    if enabled:
        _backups = _chars.copy(), _primary_style, _secondary_style
        _chars = {
            "primary": {"selected": "*", "block": "#"},
            "secondary": {"arrow": ">", "edge": "|"},
            "plain": {"unselected": "."},
        }
        _primary_style = ()
        _secondary_style = ()
    else:
        _chars, _primary_style, _secondary_style = _backups
    _ascii_mode = enabled
