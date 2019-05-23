from typing import Dict

__all__ = ["DEFAULT_CHARS"]

DEFAULT_CHARS: Dict[str, Dict[str, str]] = {
    "primary": {"arrow": "❱", "block": "█"},
    "secondary": {"selected": "●", "left-edge": "▐", "right-edge": "▌"},
    "plain": {"unselected": "○"},
}
