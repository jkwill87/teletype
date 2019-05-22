# coding=utf-8

from os import name as os_name

__all__ = ["VERSION", "IS_WINDOWS"]

VERSION = "0.3.1"

IS_WINDOWS = os_name in ("nt", "cygwin")
