from ..io import style_format as _style_format
from ..codes import chars

# These variables control module internal state; please do not modify directly
_backups = ()
_ascii_mode = False
_primary_style = ("green",)
_secondary_style = ("green", "dark")
_chars = chars.copy()


def _get_char_category(key):
    for category, d in _chars.items():
        if key in d.keys():
            return category


def _get_glyph(key):
    category = _get_char_category(key)
    if not category:
        raise KeyError
    glyph = _chars[category][key]
    if category == "primary":
        glyph = _style_format(glyph, _primary_style)
    elif category == "secondary":
        glyph = _style_format(glyph, _secondary_style)
    return glyph


def set_style(primary=None, secondary=None):
    """ Sets primary and secondary component styles.
    """
    global _primary_style, _secondary_style
    if primary:
        _primary_style = primary
    if secondary:
        _secondary_style = secondary


def set_char(key, value):
    """ Updates charters used to render components.
    """
    global _chars
    category = _get_char_category(key)
    if not category:
        raise KeyError
    _chars[category][key] = value


def ascii_mode(enabled=True):
    """ Disables color and switches to an ASCII character set if True.
    """
    global _backups, _chars, _primary_style, _secondary_style, _ascii_mode
    if not (enabled or _backups) or (enabled and _ascii_mode):
        return
    if enabled:
        _backups = _chars.copy(), _primary_style, _secondary_style
        _chars = {
            "primary": {"selected": "*", "block": "#"},
            "secondary": {"arrow": ">", "left-edge": "|", "right-edge": "|"},
            "plain": {"unselected": "."},
        }
        _primary_style = ()
        _secondary_style = ()
    else:
        _chars, _primary_style, _secondary_style = _backups
    _ascii_mode = enabled
