from os import name as os_name

__all__ = ["VERSION", "IS_WINDOWS"]

VERSION: str = "1.0.0"

IS_WINDOWS: bool = os_name in ("nt", "cygwin")
