# coding=utf-8

from os import name as os_name

__all__ = ["VERSION", "IS_WINDOWS"]

VERSION = "1.0.3"

IS_WINDOWS = os_name in ("nt", "cygwin")
