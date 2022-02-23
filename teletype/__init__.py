from os import name as os_name

from teletype.__version__ import VERSION

__all__ = ["VERSION", "IS_WINDOWS"]

IS_WINDOWS = os_name in ("nt", "cygwin")
